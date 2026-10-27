"""Run bounded cumulative integration only after the frozen matrix has finished."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import time

ROOT = Path('/data/zhuofeng-li/home/ming3-main-integration-20261027')
MATRIX = Path('/data/zhuofeng-li/home/ming3-current-main-20261027')
UUID = 'GPU-4ac09667-48f7-6a03-b930-8338f78d441e'
IMAGE = 'localhost/ming3-pr3136:20261026'
NAMES = ['ming-main-unit', 'ming-main-tiny', 'ming-main-dense', 'ming-main-quality']
assert json.loads((MATRIX / 'matrix-status.json').read_text())['stage'] == 'complete'
assert time.time() < json.loads((MATRIX / 'qualification-release.json').read_text())['lease_expires_epoch'] - 2100
assert not (ROOT / 'status.json').exists(), 'Inspect any previous attempt before restarting'
source = json.loads((ROOT / 'source/.source-manifest.json').read_text())
assert source['tree'] == '4c02de011867bef32cbec1b93f0929a219947fec'
for relative, entry in source['entries'].items():
    path = ROOT / 'source' / relative
    payload = os.readlink(path).encode() if entry['mode'] == '120000' else path.read_bytes()
    assert hashlib.sha1(b'blob ' + str(len(payload)).encode() + b'\0' + payload).hexdigest() == entry['digest'], relative
assert not subprocess.check_output(['podman', 'ps', '-q'], text=True).strip()
assert subprocess.check_output(['nvidia-smi', '--query-gpu=uuid', '--format=csv,noheader'], text=True).strip() == UUID
assert not subprocess.check_output(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'], text=True).strip()
image_id = subprocess.check_output(['podman', 'image', 'inspect', IMAGE, '--format', '{{.Id}}'], text=True).strip()
assert image_id.removeprefix('sha256:').startswith('afb9f5ee'), image_id
state = {'source': source, 'image_id': image_id, 'gpu_uuid': UUID,
         'assignment': '01M5XFE1DE8PVBQWTSDP2JDYRY', 'completed': [],
         'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
         'scope': 'Unpublished cumulative main integration, not independent PR performance or final merged-series validation'}


def save():
    state['updated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    temporary = ROOT / 'status.partial'
    temporary.write_text(json.dumps(state, indent=2) + '\n')
    temporary.replace(ROOT / 'status.json')


def run(name, command, timeout):
    assert time.time() < json.loads((MATRIX / 'qualification-release.json').read_text())['lease_expires_epoch'] - timeout - 120
    state['stage'] = name
    save()
    (ROOT / f'{name}-command.json').write_text(json.dumps(command, indent=2) + '\n')
    with (ROOT / f'{name}.log').open('w') as log:
        result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=timeout)
    if result.returncode:
        raise RuntimeError(f'{name} exited {result.returncode}')
    state['completed'].append(name)
    save()


common = ['podman', 'run', '--rm', '--security-opt', 'label=disable', '--network=none',
          '--device', 'nvidia.com/gpu=' + UUID, '--shm-size', '32g',
          '-e', 'CUDA_VISIBLE_DEVICES=0', '-e', 'NVIDIA_VISIBLE_DEVICES=' + UUID,
          '-e', 'PYTHONDONTWRITEBYTECODE=1', '-e', 'HF_HUB_OFFLINE=1',
          '-e', 'HF_DATASETS_OFFLINE=1', '-e', 'TRANSFORMERS_OFFLINE=1',
          '-e', 'PYTHONPATH=/observe:/workspace/sglang-omni:/opt/rsi-deps/cosyvoice:/opt/rsi-deps/matcha',
          '-v', str(ROOT / 'source') + ':/workspace/sglang-omni:ro',
          '-v', str(ROOT / 'observe') + ':/observe:ro',
          '-w', '/workspace/sglang-omni', '--entrypoint', '/opt/sglang/bin/python3']
try:
    run('unit', common + ['--name', NAMES[0], IMAGE, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
        'tests/unit_test/ming3_tts', 'tests/unit_test/ming_tts', 'tests/unit_test/ming_omni',
        'tests/unit_test/ming3_asr', 'tests/unit_test/ming3_audio',
        'tests/unit_test/pipeline/test_async_decode.py',
        'tests/unit_test/pipeline/test_streaming_simple_scheduler.py',
        'tests/unit_test/scheduling/test_streaming_vocoder.py',
        'tests/unit_test/scheduling/test_streaming_vocoder_session.py',
        'tests/unit_test/models/test_model_capabilities.py', 'tests/unit_test/utils/test_checkpoint.py'], 900)
    for variant, model, name in [
        ('tiny', '/models/tiny', NAMES[1]),
        ('dense', 'inclusionAI/Ming-3.0-tts-0.5B@8d66b70a00f05ad183fa8a863b4ce609fc83cbc0', NAMES[2]),
    ]:
        run('smoke-' + variant, common + ['--name', name,
            '-v', '/data/zhuofeng-li/home/ming3-review/tiny-model:/models/tiny:ro',
            '-v', str(ROOT / 'validate_http.py') + ':/validate_http.py:ro',
            '-v', str(ROOT / 'outputs' / variant) + ':/validation:rw',
            '-e', 'MING_PR_GRAPH_EVENTS=/validation/graphs.jsonl',
            '-e', 'MING_VALIDATION_MODEL=' + model,
            '-e', 'MING_SOURCE_TREE=' + source['tree'],
            IMAGE, '/validate_http.py'], 1200)
        smoke = json.loads((ROOT / 'outputs' / variant / 'http-results.json').read_text())
        assert smoke['stage'] == 'complete' and len(smoke['cases']) == 14
        if variant == 'tiny':
            captures = [json.loads(line) for line in (ROOT / 'outputs/tiny/graphs.jsonl').read_text().splitlines()]
            assert sum(any(path.endswith('/ming3_tts/vocoder_graph.py') for path in event['stack']) for event in captures) == 250
    run('quality', common + ['--name', NAMES[3],
        '-v', str(ROOT / 'validate_quality.py') + ':/validate_quality.py:ro',
        '-v', str(ROOT / 'outputs') + ':/outputs:ro',
        '-v', str(ROOT / 'quality') + ':/quality:rw', IMAGE, '/validate_quality.py'], 600)
    quality = json.loads((ROOT / 'quality/quality-results.json').read_text())
    assert quality['stage'] == 'complete' and len(quality['cases']) == 8
    assert all(case['same_normalized_transcript'] for case in quality['cases'])
    state['stage'] = 'complete'
    save()
except BaseException as error:
    state.update(stage='failed', error=f'{type(error).__name__}: {error}')
    save()
    raise
finally:
    cleanup = []
    for name in NAMES:
        if subprocess.run(['podman', 'container', 'exists', name]).returncode == 0:
            stopped = subprocess.run(['podman', 'stop', '--time', '10', name])
            cleanup.append({'container': name, 'stop_exit': stopped.returncode})
    state['cleanup'] = cleanup
    save()
