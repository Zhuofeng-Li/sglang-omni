"""Bounded functional validation after the frozen H100 matrix completes."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import time

root = Path('/data/zhuofeng-li/home/ming3-tiny-stream-integration-20261027')
source = '8d0f5d4352b704986cbc50e44ec4df42cce0fbc9'
uuid = 'GPU-7cea2752-34c7-f9c2-cd45-79163c61c398'
image = 'localhost/ming3-pr3136:20261026'
assert json.loads(Path('/data/zhuofeng-li/home/ming3-pr3136-review-20261026/matrix-status.json').read_text())['stage'] == 'complete'
assert json.loads((root / 'source/.source-manifest.json').read_text())['source'] == source
assert not subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'], text=True).strip()
state = {'source': source, 'assignment': '01M5W7M9EJYACXJ5D8BNMPC46X',
         'gpu_uuid': uuid, 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'completed': [], 'scope': 'Functional validation only; not a performance comparison'}
if (root / 'status.json').exists():
    previous = json.loads((root / 'status.json').read_text())
    assert previous['stage'] == 'failed' and previous['completed'] == ['unit']
    assert 'offline mode is enabled' in (root / 'download.log').read_text()
    state = {key: value for key, value in previous.items() if key != 'error'}
    state['resumed_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    state['resume_reason'] = 'Explicitly disable inherited offline mode for asset download'


def save():
    state['updated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    temporary = root / 'status.partial'
    temporary.write_text(json.dumps(state, indent=2) + '\n')
    temporary.replace(root / 'status.json')


def run(name, command, timeout):
    state['stage'] = name
    save()
    (root / f'{name}-command.json').write_text(json.dumps(command, indent=2))
    with (root / f'{name}.log').open('w') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'{name}: exit {result.returncode}')
    state['completed'].append(name)
    save()


common = ['podman', 'run', '--rm', '--network=none', '--security-opt', 'label=disable',
          '--device', 'nvidia.com/gpu=' + uuid, '--shm-size', '32g',
          '-e', 'CUDA_VISIBLE_DEVICES=0', '-e', 'NVIDIA_VISIBLE_DEVICES=' + uuid,
          '-e', 'PYTHONDONTWRITEBYTECODE=1', '-e', 'HF_HUB_OFFLINE=1',
          '-e', 'HF_DATASETS_OFFLINE=1', '-e', 'TRANSFORMERS_OFFLINE=1',
          '-e', 'PYTHONPATH=/observe:/workspace/sglang-omni:/opt/rsi-deps/cosyvoice:/opt/rsi-deps/matcha',
          '-v', str(root / 'source') + ':/workspace/sglang-omni:ro',
          '-v', str(root / 'observe') + ':/observe:ro',
          '-w', '/workspace/sglang-omni', '--entrypoint', '/opt/sglang/bin/python3']
try:
    if 'unit' not in state['completed']:
        run('unit', common + ['--name', 'ming-tiny-graph-stream-unit',
            '-v', str(root / 'unit') + ':/validation:rw',
            '-e', 'MING_PR_GRAPH_EVENTS=/validation/graphs.jsonl', image,
            '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
            'tests/unit_test/ming3_tts', 'tests/unit_test/ming_tts',
            'tests/unit_test/mps', 'tests/unit_test/utils/test_cpu.py',
            'tests/unit_test/pipeline/test_simple_scheduler_concurrent.py',
            'tests/unit_test/pipeline/test_stage_process_env.py'], 900)
    run('download', ['podman', 'run', '--rm', '--network=host',
        '--name', 'ming-tiny-graph-stream-assets',
        '-e', 'CUDA_VISIBLE_DEVICES=', '-e', 'NVIDIA_VISIBLE_DEVICES=void',
        '-e', 'HF_HUB_OFFLINE=0', '-e', 'HF_DATASETS_OFFLINE=0',
        '-e', 'TRANSFORMERS_OFFLINE=0',
        '-e', 'HF_HOME=/assets/hf-cache', '-v', str(root / 'assets') + ':/assets:rw',
        '--entrypoint', '/opt/sglang/bin/hf', image,
        'download', 'inclusionAI/Ming-3.0-tts-tiny',
        '--revision', '7bd9446a8d47e462362261a0150258da6d458318',
        '--local-dir', '/assets/tiny', '--max-workers', '4', '--format', 'json'], 1200)
    run('smoke', common + ['--name', 'ming-tiny-graph-stream-smoke',
        '-v', str(root / 'assets/tiny') + ':/models/tiny:ro',
        '-v', str(root / 'validate_http.py') + ':/validate_http.py:ro',
        '-v', str(root / 'smoke-tiny') + ':/validation:rw',
        '-e', 'MING_PR_GRAPH_EVENTS=/validation/graphs.jsonl',
        '-e', 'MING_EXPECTED_GPU_UUID=' + uuid, '-e', 'MING_SOURCE_COMMIT=' + source,
        '-e', 'MING_VALIDATION_MODEL=/models/tiny', image, '/validate_http.py'], 1200)
    smoke = json.loads((root / 'smoke-tiny/http-results.json').read_text())
    assert smoke['stage'] == 'complete' and len(smoke['cases']) == 14
    captures = [json.loads(line) for line in (root / 'smoke-tiny/graphs.jsonl').read_text().splitlines()]
    assert sum(any(path.endswith('/ming3_tts/vocoder_graph.py') for path in event['stack']) for event in captures) == 250
    run('quality', common + ['--name', 'ming-tiny-graph-stream-quality',
        '-v', str(root / 'validate_quality.py') + ':/validate_quality.py:ro',
        '-v', str(root / 'smoke-tiny') + ':/outputs/tiny:ro',
        '-v', str(root / 'quality') + ':/quality:rw', image, '/validate_quality.py'], 600)
    quality = json.loads((root / 'quality/quality-results.json').read_text())
    assert quality['stage'] == 'complete' and len(quality['cases']) == 4
    assert all(row['same_normalized_transcript'] for row in quality['cases'])
    state['stage'] = 'complete'
    save()
except BaseException as error:
    state.update(stage='failed', error=f'{type(error).__name__}: {error}')
    save()
    raise
finally:
    for name in ['ming-tiny-graph-stream-unit', 'ming-tiny-graph-stream-assets',
                 'ming-tiny-graph-stream-smoke', 'ming-tiny-graph-stream-quality']:
        if subprocess.run(['podman', 'container', 'exists', name]).returncode == 0:
            subprocess.run(['podman', 'stop', '--time', '10', name], check=True)
