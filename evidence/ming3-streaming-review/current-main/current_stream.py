"""Check current-main HTTP integration and remeasure affected dense preprocessing."""
from pathlib import Path
import datetime
import json
import subprocess

root = Path('/data/zhuofeng-li/home/ming3-current-main-20261027')
assets = Path('/data/zhuofeng-li/home/ming3-review')
uuid = 'GPU-4ac09667-48f7-6a03-b930-8338f78d441e'
image = 'localhost/ming3-pr3136:20261026'
source = '348f6973d4878ed77a9c6c60d072c91addaf15d8'
state = {'stage': 'preflight', 'completed': [], 'source': source}


def save():
    state['updated_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    (root / 'stream-status.json').write_text(json.dumps(state, indent=2))


def run(name, command):
    state['stage'] = name
    save()
    with (root / (name + '.log')).open('w') as log:
        outcome = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
    if outcome.returncode:
        raise RuntimeError(f'{name}: exit {outcome.returncode}')
    state['completed'].append(name)
    save()


assert json.loads((root / 'test-status.json').read_text())['stage'] == 'passed'
common = ['podman', 'run', '--rm', '--network=none', '--security-opt', 'label=disable',
          '--device', 'nvidia.com/gpu=' + uuid, '--shm-size', '32g',
          '-e', 'CUDA_VISIBLE_DEVICES=0', '-e', 'NVIDIA_VISIBLE_DEVICES=' + uuid,
          '-e', 'PYTHONDONTWRITEBYTECODE=1',
          '-e', 'PYTHONPATH=/workspace/sglang-omni:/opt/rsi-deps/cosyvoice:/opt/rsi-deps/matcha',
          '-v', str(root / 'stream') + ':/workspace/sglang-omni:ro',
          '-v', str(assets / 'tiny-model') + ':/models/tiny:ro',
          '-w', '/workspace/sglang-omni', '--entrypoint', '/opt/sglang/bin/python3']
save()
try:
    for variant in ['dense', 'tiny']:
        output = root / ('smoke-' + variant)
        output.mkdir(exist_ok=True)
        model = '/models/tiny' if variant == 'tiny' else '/opt/rsi-assets/huggingface/hub/models--inclusionAI--Ming-3.0-tts-0.5B/snapshots/8d66b70a00f05ad183fa8a863b4ce609fc83cbc0'
        run('smoke-' + variant, common + ['--name', 'ming-current-smoke-' + variant,
            '-v', str(root / 'validate_integration.py') + ':/validate_http.py:ro',
            '-v', str(output) + ':/validation:rw', '-e', 'MING_VALIDATION_MODEL=' + model,
            '-e', 'MING_VALIDATION_ARM=candidate', image, '/validate_http.py'])
    output = root / 'metrics-dense'
    output.mkdir(exist_ok=True)
    run('measure-dense', common + ['--name', 'ming-current-measure-dense',
        '-v', str(root / 'measure.py') + ':/measure.py:ro', '-v', str(output) + ':/results:rw',
        '-e', 'MING_VARIANT=dense', '-e', 'MING_SOURCE_COMMIT=' + source,
        '-e', 'TRITON_CACHE_DIR=/results/triton-cache', '-e', 'TORCHINDUCTOR_CACHE_DIR=/results/inductor-cache',
        image, '/measure.py'])
    output = root / 'smoke-quality'
    output.mkdir(exist_ok=True)
    run('quality', common + ['--name', 'ming-current-quality',
        '-v', str(root / 'validate_quality.py') + ':/validate_quality.py:ro',
        '-v', str(root / 'smoke-dense') + ':/outputs/dense:ro',
        '-v', str(root / 'smoke-tiny') + ':/outputs/tiny:ro', '-v', str(output) + ':/quality:rw',
        image, '/validate_quality.py'])
    state['stage'] = 'complete'
    save()
except BaseException as error:
    state.update(stage='failed', error=f'{type(error).__name__}: {error}')
    save()
    raise
