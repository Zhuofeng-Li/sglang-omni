"""Transcribe every scoped paired waveform without dropping capped outputs."""
from pathlib import Path
import io
import json
import os
import signal
import subprocess
import sys
import time
import wave

import httpx
import pyarrow.parquet as parquet
from jiwer import process_words

from benchmarks.tasks.asr import normalize_text

root = Path('/quality')
root.mkdir(exist_ok=True)
model = '/opt/rsi-assets/huggingface/hub/models--Qwen--Qwen3-ASR-1.7B/snapshots/7278e1e70fe206f11671096ffdd38061171dd6e5'
assert Path(model).is_dir(), model
report = {'model': model, 'revision': '7278e1e70fe206f11671096ffdd38061171dd6e5',
          'stage': 'starting', 'cases': [], 'normalization': 'benchmarks.tasks.asr.normalize_text; ZH character based'}
command = [sys.executable, '-m', 'sglang_omni.cli', 'serve', '--model-path', model,
           '--host', '127.0.0.1', '--port', '18882', '--mem-fraction-static', '0.5',
           '--asr.engine.enable_torch_compile', 'false', '--asr.engine.max_running_requests', '8',
           '--asr.engine.cuda_graph_max_bs', '8']
report['command'] = command


def save():
    (root / 'quality-results.json').write_text(json.dumps(report, indent=2, ensure_ascii=False))


dataset = Path('/opt/rsi-assets/huggingface/hub/datasets--zhaochenyang20--seed-tts-eval-arrow/snapshots/27f4c1adee83b5b29b7c4b375f6b976324bda308/data')
targets = {language: parquet.read_table(dataset / f'{language}-00000-of-00001.parquet').slice(0, 1).to_pylist()[0]['target_text'] for language in ['en', 'zh']}
save()
with (root / 'asr-server.log').open('w') as log:
    server = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    try:
        with httpx.Client(base_url='http://127.0.0.1:18882', timeout=180) as client:
            for _ in range(600):
                if server.poll() is not None:
                    raise RuntimeError(f'ASR server exited {server.returncode}')
                try:
                    if client.get('/health', timeout=2).status_code == 200:
                        break
                except httpx.HTTPError:
                    pass
                time.sleep(1)
            else:
                raise TimeoutError('ASR server startup timeout')
            for variant in ['dense', 'tiny']:
                for language in ['en', 'zh']:
                    for reference in [0, 1]:
                        result = {'model': variant, 'language': language, 'reference': reference,
                                  'target': targets[language], 'outputs': {}}
                        for mode in ['offline', 'stream']:
                            samples = (Path('/outputs') / variant / f'{language}-reference{reference}-{mode}.pcm').read_bytes()
                            buffer = io.BytesIO()
                            with wave.open(buffer, 'wb') as wav:
                                wav.setnchannels(1)
                                wav.setsampwidth(2)
                                wav.setframerate(44100)
                                wav.writeframes(samples)
                            response = client.post('/v1/audio/transcriptions',
                                data={'model': model, 'language': language},
                                files={'file': ('speech.wav', buffer.getvalue(), 'audio/wav')})
                            assert response.status_code == 200, response.text
                            transcript = response.json()['text']
                            reference_text = normalize_text(targets[language], language)
                            hypothesis = normalize_text(transcript, language)
                            score = process_words(reference_text, hypothesis)
                            result['outputs'][mode] = {'transcript': transcript, 'wer_or_cer': score.wer,
                                'errors': score.substitutions + score.deletions + score.insertions,
                                'reference_units': score.substitutions + score.deletions + score.hits}
                        result['same_normalized_transcript'] = normalize_text(result['outputs']['offline']['transcript'], language) == normalize_text(result['outputs']['stream']['transcript'], language)
                        report['cases'].append(result)
                        save()
        report['stage'] = 'complete'
        save()
    except BaseException as error:
        report.update(stage='failed', error=f'{type(error).__name__}: {error}')
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
