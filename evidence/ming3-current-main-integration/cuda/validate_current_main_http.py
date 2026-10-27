"""Scoped functional validation of the Ming3 speech endpoint."""
import asyncio
import base64
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import httpx
import numpy as np
import pyarrow.parquet as parquet
import torch
import sglang_omni

ROOT = Path('/validation')
MODEL = os.environ['MING_VALIDATION_MODEL']
ARM = os.environ.get('MING_VALIDATION_ARM', 'candidate')
ROOT.mkdir(exist_ok=True, parents=True)
summary = {'model': MODEL, 'arm': ARM, 'cases': [], 'started': time.time(),
           'gpu': torch.cuda.get_device_name(0),
           'gpu_uuid': str(torch.cuda.get_device_properties(0).uuid),
           'versions': {name: importlib.metadata.version(name) for name in
                        ['torch', 'transformers', 'sglang', 'diffusers']}}
summary['source_tree'] = os.environ['MING_SOURCE_TREE']
assert summary['source_tree'] == '4c02de011867bef32cbec1b93f0929a219947fec'
summary['source_import'] = str(Path(sglang_omni.__file__).resolve())
assert summary['source_import'].startswith('/workspace/sglang-omni/')
assert torch.cuda.device_count() == 1
assert summary['gpu_uuid'].removeprefix('GPU-') == '4ac09667-48f7-6a03-b930-8338f78d441e'
for package, expected in [('torch', '2.14.1'), ('transformers', '5.19.0'), ('sglang', '0.5.22')]:
    assert summary['versions'][package].split('+')[0] == expected
command = [sys.executable, '-m', 'sglang_omni.cli', 'serve', '--model-path', MODEL,
           '--host', '127.0.0.1', '--port', '18881', '--mem-fraction-static', '0.6',
           '--tts_engine.engine.max_running_requests', '32',
           '--tts_engine.engine.cuda_graph_max_bs', '32']
summary['server_command'] = command
dataset = Path('/opt/rsi-assets/huggingface/hub/datasets--zhaochenyang20--seed-tts-eval-arrow/snapshots/27f4c1adee83b5b29b7c4b375f6b976324bda308/data')
corpus = {language: parquet.read_table(dataset / f'{language}-00000-of-00001.parquet').slice(0, 2).to_pylist()
          for language in ['en', 'zh']}


def save():
    (ROOT / 'http-results.json').write_text(json.dumps(summary, indent=2))


def make_request(language, sample_index, with_reference, stream):
    sample = corpus[language][sample_index]
    request = {'model': MODEL, 'input': sample['target_text'], 'response_format': 'pcm',
               'stream': stream, 'seed': 42, 'max_new_tokens': 250}
    if with_reference:
        request['references'] = [{'data': base64.b64encode(sample['ref_audio']['bytes']).decode(),
                                  'media_type': 'audio/wav', 'text': sample['ref_text']}]
    return request


async def generate(client, request, case_name):
    started = time.perf_counter()
    pieces = []
    timings = []
    async with client.stream('POST', '/v1/audio/speech', json=request, timeout=180) as response:
        if response.status_code != 200:
            raise RuntimeError(f'{case_name}: HTTP {response.status_code}: {(await response.aread())[:4000]!r}')
        headers = dict(response.headers)
        async for piece in response.aiter_raw():
            pieces.append(piece)
            timings.append(time.perf_counter() - started)
    waveform_bytes = b''.join(pieces)
    waveform = np.frombuffer(waveform_bytes, dtype='<i2')
    assert waveform.size > 0 and np.isfinite(waveform).all()
    (ROOT / f'{case_name}.pcm').write_bytes(waveform_bytes)
    result = {'case': case_name, 'status': 200, 'chunks': len(pieces), 'samples': len(waveform),
              'chunk_bytes': list(map(len, pieces)), 'chunk_times_seconds': timings,
              'response_seconds': time.perf_counter() - started,
              'sha256': hashlib.sha256(waveform_bytes).hexdigest(), 'headers': headers}
    if request['stream']:
        request_id = headers['x-request-id']
        outcome = await client.get(f'/v1/audio/speech/{request_id}')
        result['outcome_status'] = outcome.status_code
        assert outcome.status_code == 200, outcome.text
        result['outcome'] = outcome.json()
        assert result['outcome']['finish_reason'] in ['stop', 'length'], result['outcome']
    summary['cases'].append(result)
    save()
    return waveform


async def run():
    async with httpx.AsyncClient(base_url='http://127.0.0.1:18881', timeout=180) as client:
        for language in ['en', 'zh']:
            for with_reference in [False, True]:
                name = f'{language}-reference{int(with_reference)}'
                offline = await generate(client, make_request(language, 0, with_reference, False), name + '-offline')
                if ARM == 'base':
                    continue
                streamed = await generate(client, make_request(language, 0, with_reference, True), name + '-stream')
                comparison = {'case': name, 'offline_samples': len(offline), 'stream_samples': len(streamed)}
                assert offline.shape == streamed.shape, comparison
                comparison.update(pcm_max_absolute_delta=int(np.abs(offline.astype('int32') - streamed.astype('int32')).max()),
                                  pcm_mean_absolute_delta=float(np.abs(offline.astype('int32') - streamed.astype('int32')).mean()),
                                  correlation=float(np.corrcoef(offline, streamed)[0, 1]))
                summary.setdefault('comparisons', []).append(comparison)
                save()
        if ARM != 'base':
            request = make_request('en', 0, True, True)
            request['stream_format'] = 'sse'
            events = []
            async with client.stream('POST', '/v1/audio/speech', json=request) as response:
                assert response.status_code == 200, await response.aread()
                async for line in response.aiter_lines():
                    if line.startswith('data: '):
                        events.append(json.loads(line[6:]))
            assert events[-1]['type'] == 'speech.audio.done', events[-1]
            assert events[-1]['usage']['output_tokens'] > 0, events[-1]
            assert events[-1]['finish_reason'] in ['stop', 'length'], events[-1]
            assert all(event['type'] == 'speech.audio.delta' for event in events[:-1])
            assert sum(len(base64.b64decode(event['audio'])) for event in events[:-1]) > 0
            summary['sse'] = {'audio_chunks': len(events) - 1, 'terminal': events[-1]}
            save()
            await asyncio.gather(*[generate(client, make_request(language, 1, True, True), f'concurrent-{index}-{language}')
                                  for index, language in enumerate(['en', 'zh', 'en', 'zh'])])
            cancel_request = make_request('en', 0, True, True)
            cancel_request['input'] *= 4
            async with client.stream('POST', '/v1/audio/speech', json=cancel_request) as response:
                assert response.status_code == 200, await response.aread()
                async for chunk in response.aiter_raw():
                    assert chunk
                    break
            summary['disconnect_after_first_chunk'] = True
            await generate(client, make_request('en', 1, False, True), 'after-disconnect')
            short_request = make_request('en', 1, False, True)
            short_request['max_new_tokens'] = 1
            await generate(client, short_request, 'one-latent-length-stop')
        summary['stage'] = 'complete'
        save()


save()
with (ROOT / 'server.log').open('w') as server_log:
    server = subprocess.Popen(command, stdout=server_log, stderr=subprocess.STDOUT, start_new_session=True)
    summary['server_pid'] = server.pid
    try:
        with httpx.Client(base_url='http://127.0.0.1:18881', timeout=2) as client:
            for _ in range(600):
                if server.poll() is not None:
                    raise RuntimeError(f'Server exited {server.returncode}')
                try:
                    response = client.get('/health')
                    if response.status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(1)
            else:
                raise TimeoutError('Server startup timed out')
        summary['startup_seconds'] = time.time() - summary['started']
        asyncio.run(run())
    except BaseException as error:
        summary.update(stage='failed', error=f'{type(error).__name__}: {error}')
        save()
        raise
    finally:
        if server.poll() is None:
            os.killpg(server.pid, signal.SIGTERM)
            try:
                server.wait(timeout=30)
            except subprocess.TimeoutExpired:
                os.killpg(server.pid, signal.SIGKILL)
                server.wait()
        summary['server_exit'] = server.returncode
        save()
