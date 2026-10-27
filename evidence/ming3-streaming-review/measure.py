"""Measure native first-audio and playback continuity at the reviewed defaults."""
import importlib.metadata
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import urllib.request

import torch
import sglang_omni

root = Path('/results')
variant = os.environ['MING_VARIANT']
model = '/models/tiny' if variant == 'tiny' else '/opt/rsi-assets/huggingface/hub/models--inclusionAI--Ming-3.0-tts-0.5B/snapshots/8d66b70a00f05ad183fa8a863b4ce609fc83cbc0'
state = {'variant': variant, 'started': time.time(), 'completed': [], 'stage': 'preflight',
         'gpu': torch.cuda.get_device_name(0), 'gpu_uuid': str(torch.cuda.get_device_properties(0).uuid),
         'source_commit': os.environ['MING_SOURCE_COMMIT'],
         'versions': {name: importlib.metadata.version(name) for name in ['torch','transformers','sglang']},
         'model_path': model, 'max_samples': 128, 'seeds':[42,43], 'concurrencies':[1,32]}
state['source_import'] = str(Path(sglang_omni.__file__).resolve())
assert state['source_import'].startswith('/workspace/sglang-omni/')
assert torch.cuda.device_count() == 1
assert state['gpu_uuid'].removeprefix('GPU-').lower() == '4ac09667-48f7-6a03-b930-8338f78d441e'
assert state['versions']['transformers'] == '5.19.0'
assert state['versions']['sglang'] == '0.5.22'
def save():
    state['updated'] = time.time()
    temporary = root/'status.partial'; temporary.write_text(json.dumps(state,indent=2)); temporary.replace(root/'status.json')
root.mkdir(exist_ok=True)
command=[sys.executable,'-m','sglang_omni.cli','serve','--model-path',model,'--host','127.0.0.1','--port','18881',
         '--tts_engine.engine.max_running_requests','32','--tts_engine.engine.cuda_graph_max_bs','32']
state['server_command']=command
save()
with (root/'server.log').open('w') as log:
    server=subprocess.Popen(command,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    try:
        deadline=time.monotonic()+1200
        while time.monotonic()<deadline:
            if server.poll() is not None: raise RuntimeError(f'server exited {server.returncode}')
            try:
                with urllib.request.urlopen('http://127.0.0.1:18881/health',timeout=2) as response:
                    if response.status==200:break
            except Exception:time.sleep(2)
        else:raise TimeoutError('server readiness')
        state['startup_s']=time.time()-state['started'];save()
        for language in ['en','zh']:
            for concurrency in [1,32]:
                for mode,seed in [('nonstream',42),('stream',42),('stream',43),('nonstream',43)]:
                    name=f'{language}-c{concurrency}-{mode}-s{seed}'
                    output=root/name;output.mkdir()
                    state.update(stage='benchmark',active=name);save()
                    benchmark=[sys.executable,'-m','benchmarks.eval.benchmark_tts_seedtts',
                        '--model',model,'--meta','zhaochenyang20/seed-tts-eval-arrow',
                        '--port','18881','--host','127.0.0.1','--use-existing-server','--generate-only',
                        '--lang',language,'--max-samples','128','--seed',str(seed),
                        '--max-concurrency',str(concurrency),'--warmup',str(concurrency),
                        '--max-running-requests','32','--cuda-graph-max-bs','32',
                        '--output-dir',str(output)]
                    if mode=='stream':benchmark+=['--stream']
                    (output/'command.json').write_text(json.dumps(benchmark))
                    with (output/'execution.log').open('w') as result_log:
                        result=subprocess.run(benchmark,stdout=result_log,stderr=subprocess.STDOUT)
                    if result.returncode:raise RuntimeError(f'{name} failed: {result.returncode}')
                    report=json.loads((output/'speed_results.json').read_text())
                    assert len(report['per_request']) == 128, report['summary']
                    assert all(row['is_success'] for row in report['per_request']), report['summary']
                    if mode == 'stream':
                        assert all(row['audio_ttfp_s'] is not None for row in report['per_request'])
                    state['completed'].append(name);save()
        state.update(stage='complete',finished=time.time());save()
    except BaseException as error:
        state.update(stage='failed',error=f'{type(error).__name__}: {error}');save();raise
    finally:
        os.killpg(server.pid,signal.SIGTERM)
        try:server.wait(timeout=30)
        except subprocess.TimeoutExpired:
            os.killpg(server.pid,signal.SIGKILL);server.wait()
