"""Supplementary PR qualification; frozen research evaluator stays unchanged."""
from pathlib import Path
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time

import yaml

import numpy as np
import onnxruntime
import pyarrow.parquet as parquet
import torch

from sglang_omni.config.manager import ConfigManager
from sglang_omni.config.sources import dump_user_config
from sglang_omni.utils.audio import load_audio
from sglang_omni.utils.audio_features import cached_fbank

root = Path('/results')
config = json.loads((root / 'config.json').read_text())
cache = root / 'cache'
cache.mkdir(exist_ok=True)
env = dict(os.environ)
for name, folder in {
    'TMPDIR': 'tmp', 'XDG_CACHE_HOME': 'xdg',
    'TORCH_HOME': 'torch', 'TRITON_CACHE_DIR': 'triton',
    'SGLANG_CACHE_DIR': 'sglang', 'SGLANG_JIT_CACHE_DIR': 'sglang-jit',
    'SGLANG_CUTE_AOT_CACHE_DIR': 'sglang-cute',
    'CUDA_CACHE_PATH': 'cuda', 'TORCHINDUCTOR_CACHE_DIR': 'inductor',
    'FLASHINFER_WORKSPACE_BASE': 'flashinfer', 'TORCH_EXTENSIONS_DIR': 'extensions',
    'HF_DATASETS_CACHE': 'datasets', 'HF_MODULES_CACHE': 'hf-modules',
}.items():
    directory = cache / folder
    directory.mkdir(exist_ok=True)
    env[name] = str(directory)
shutil.copytree('/opt/rsi-assets/huggingface/datasets', cache / 'datasets',
                symlinks=True, dirs_exist_ok=True)
env.update(PYTHONPATH='/observe:/workspace/sglang-omni:/opt/rsi-deps/cosyvoice:/opt/rsi-deps/matcha',
           MING_PR_GRAPH_EVENTS='/results/graphs.jsonl', PYTHONUNBUFFERED='1')
command = [sys.executable, '-m', 'benchmarks.eval.benchmark_tts_seedtts',
           '--meta', 'zhaochenyang20/seed-tts-eval-arrow',
           '--model', 'inclusionAI/Ming-3.0-tts-0.5B',
           '--port', '8000', '--output-dir', '/results/output',
           '--lang', config['language'], '--max-concurrency', str(config['concurrency']),
           '--seed', str(config['seed']), '--max-running-requests', '64',
           '--cuda-graph-max-bs', '64']
model_spec = 'inclusionAI/Ming-3.0-tts-0.5B@8d66b70a00f05ad183fa8a863b4ce609fc83cbc0'
resolved_defaults = ConfigManager.from_model_path(model_spec).config
expected_pipeline = dump_user_config(resolved_defaults)
# Full exports also contain internal topology; write only supported overrides.
pipeline = {'config_cls': expected_pipeline['config_cls'], 'model_path': model_spec}
variant = config.get('variant', 'native')
if variant == 'mps-off':
    pipeline['mps'] = 'off'
    expected_pipeline['mps'] = 'off'
elif variant == 'cache-off':
    pipeline['stages'] = {'preprocessing': {'factory': {'reference_cache_entries': 0}}}
    expected_pipeline['stages']['preprocessing']['factory']['reference_cache_entries'] = 0
elif variant == 'fused-off':
    pipeline['stages'] = {'tts_engine': {'factory': {'enable_fused_flow_head': False}}}
    expected_pipeline['stages']['tts_engine']['factory']['enable_fused_flow_head'] = False
elif variant != 'native':
    raise ValueError(variant)
(root / 'server-config.yaml').write_text(yaml.safe_dump(pipeline, sort_keys=False))
resolved_pipeline = ConfigManager.from_file('/results/server-config.yaml').config
round_trip = dump_user_config(resolved_pipeline)
assert round_trip == expected_pipeline
(root / 'resolved-pipeline.json').write_text(json.dumps(round_trip, indent=2))
command += ['--server-config', '/results/server-config.yaml']
(root / 'command.json').write_text(json.dumps(command))
preflight = '''import importlib.metadata,json,os
from pathlib import Path
import torch,sglang_omni
assert torch.cuda.is_available() and torch.cuda.device_count()==1
uuid=str(torch.cuda.get_device_properties(0).uuid)
assert uuid.removeprefix('GPU-').lower()==EXPECTED_UUID.removeprefix('GPU-').lower()
assert str(Path(sglang_omni.__file__).resolve()).startswith('/workspace/sglang-omni/')
print(json.dumps({'gpu_uuid':uuid,'gpu':torch.cuda.get_device_name(0),'import':sglang_omni.__file__,
 'versions':{name:importlib.metadata.version(name) for name in ['sglang','torch','transformers','flashinfer-python']},
 'cpu_affinity':sorted(os.sched_getaffinity(0))}))
'''.replace('EXPECTED_UUID', repr(config['gpu_uuid']))
probe = subprocess.run([sys.executable, '-c', preflight], env=env,
                       capture_output=True, text=True, check=True)
(root / 'runtime.json').write_text(probe.stdout)
samples = []
stopped = threading.Event()


def sample_memory():
    while not stopped.is_set():
        result = subprocess.run(['nvidia-smi', '--query-gpu=uuid,memory.used',
                                 '--format=csv,noheader,nounits'], capture_output=True, text=True)
        samples.append({'epoch': time.time(), 'output': result.stdout, 'exit_code': result.returncode})
        stopped.wait(1)


observer = threading.Thread(target=sample_memory)
observer.start()
try:
    with (root / 'benchmark.log').open('w') as log:
        outcome = subprocess.run(command, cwd='/workspace/sglang-omni', env=env,
                                 stdout=log, stderr=subprocess.STDOUT, timeout=10800)
finally:
    stopped.set()
    observer.join()
    (root / 'memory.json').write_text(json.dumps(samples))
if outcome.returncode:
    raise RuntimeError(f'Native benchmark failed with exit {outcome.returncode}')
speed = json.loads((root / 'output/speed_results.json').read_text())
wer = json.loads((root / 'output/wer_results.json').read_text())
hub = Path('/opt/rsi-assets/huggingface/hub')
dataset = hub / 'datasets--zhaochenyang20--seed-tts-eval-arrow/snapshots/27f4c1adee83b5b29b7c4b375f6b976324bda308'
corpus = parquet.read_table(dataset / f'data/{config["language"]}-00000-of-00001.parquet').to_pylist()
expected_ids = [row['sample_id'] for row in corpus]
requests = speed['per_request']
assert speed['config']['concurrency'] == config['concurrency']
assert speed['config']['seed'] == config['seed']
assert speed['config']['stream'] is False
assert speed['config']['max_samples'] is None
assert speed['config']['max_running_requests'] == 64
assert speed['config']['cuda_graph_max_bs'] == 64
assert [row['id'] for row in requests] == expected_ids
assert speed['summary']['total_requests'] == len(corpus)
assert speed['summary']['completed_requests'] == len(corpus)
assert speed['summary']['failed_requests'] == 0
assert all(row['is_success'] for row in requests)
assert wer['summary']['evaluated'] == len(corpus) and wer['summary']['skipped'] == 0
options = onnxruntime.SessionOptions()
options.intra_op_num_threads = 2
options.inter_op_num_threads = 1
encoder = onnxruntime.InferenceSession(str(hub / 'models--inclusionAI--Ming-3.0-tts-0.5B/snapshots/8d66b70a00f05ad183fa8a863b4ce609fc83cbc0/campplus.onnx'),
                                     sess_options=options, providers=['CPUExecutionProvider'])
input_name = encoder.get_inputs()[0].name
torch.set_num_threads(2)
similarities = []
for row in corpus:
    vectors = []
    for audio in [row['ref_audio']['bytes'], str(root / 'output/audio' / (row['sample_id'] + '.wav'))]:
        waveform = torch.from_numpy(load_audio(audio, target_sample_rate=16000))
        features = cached_fbank(waveform[None], num_mel_bins=80, sample_frequency=16000)
        features = features - features.mean(dim=0, keepdim=True)
        vectors.append(encoder.run(None, {input_name: features[None].numpy()})[0].reshape(-1))
    similarity = float(np.dot(vectors[0], vectors[1]) / (np.linalg.norm(vectors[0]) * np.linalg.norm(vectors[1])))
    assert np.isfinite(similarity)
    similarities.append(similarity)
(root / 'speaker_similarity.json').write_text(json.dumps([
    {'id': sample_id, 'similarity': similarity}
    for sample_id, similarity in zip(expected_ids, similarities, strict=True)
]))
(root / 'audio_sha256.json').write_text(json.dumps({
    sample_id: hashlib.sha256(
        (root / 'output/audio' / (sample_id + '.wav')).read_bytes()
    ).hexdigest()
    for sample_id in expected_ids
}))
result = {'config': config, 'speed': speed['summary'], 'wer': wer['summary'],
          'speaker_sim': {'mean': float(np.mean(similarities)), 'samples': len(similarities),
                          'method': 'pinned CAM++ cosine; 16kHz native fbank'},
          'coverage': len(corpus), 'finished_utc': datetime.datetime.now(datetime.timezone.utc).isoformat()}
events = []
for line in (root / 'benchmark.log').read_text(errors='replace').splitlines():
    match = re.search(r'(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d+) .*?(Starting server:|Service is ready\.|Stopping server)', line)
    if match:
        events.append({'epoch': datetime.datetime.strptime(match[1], '%Y-%m-%d %H:%M:%S,%f').timestamp(),
                       'event': match[2], 'line': line})
starts = [event for event in events if event['event'] == 'Starting server:']
if starts:
    tts_start = starts[0]['epoch']
    ready = next((event['epoch'] for event in events if event['epoch'] >= tts_start and event['event'] == 'Service is ready.'), None)
    stopped_at = next((event['epoch'] for event in events if event['epoch'] >= tts_start and event['event'] == 'Stopping server'), None)
    if ready is not None and stopped_at is not None:
        graph_path = root / 'graphs.jsonl'
        graphs = [json.loads(line) for line in graph_path.read_text().splitlines()] if graph_path.exists() else []
        memory_mib = []
        for sample in samples:
            if tts_start <= sample['epoch'] <= stopped_at:
                for line in sample['output'].splitlines():
                    gpu, used = line.split(',')
                    if gpu.strip() == config['gpu_uuid']:
                        memory_mib.append(float(used))
        result['costs'] = {'startup_to_ready_s': ready - tts_start,
                           'peak_tts_device_gib': max(memory_mib) / 1024 if memory_mib else None,
                           'successful_tts_captures': sum(tts_start <= event['epoch'] <= stopped_at for event in graphs) if graph_path.exists() else None,
                           'memory_sampling_interval_s': 1,
                           'events': events}
result['reference_cache_logs'] = [line for line in (root / 'benchmark.log').read_text(errors='replace').splitlines() if 'Ming 3 TTS' in line and 'reference encode stats' in line]
result['mps_lifecycle_logs'] = [line for line in (root / 'benchmark.log').read_text(errors='replace').splitlines() if 'mps' in line.lower() and any(word in line.lower() for word in ['start', 'daemon', 'verify', 'client', 'stop', 'cleanup'])]
(root / 'result.json').write_text(json.dumps(result, indent=2))
