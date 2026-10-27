"""Independently audit completed current-main performance cells from backup."""
from pathlib import Path
import argparse
import datetime
import json
import math
import statistics
import tarfile

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('archive', type=Path)
args = parser.parse_args()
files = {}
with tarfile.open(args.archive, 'r:gz') as archive:
    for member in archive:
        if member.isfile() and member.name.endswith(('.json', '.jsonl')):
            raw = archive.extractfile(member).read()
            files[member.name] = ([json.loads(line) for line in raw.splitlines() if line]
                                 if member.name.endswith('.jsonl') else json.loads(raw))
release = files['qualification-release.json']
assert release['candidate_commit'] == '3f8593f4cae19fe1c71e929a854bdc03b2c185e6'
assert release['base'] == '0fe60cf6c102caf982430e1764243c6e5c749d76'
plan = {row['id']: row for row in files['plan.json']}
state = files['matrix-status.json']
results, reference_ids, versions = {}, {}, set()
for identity in state['completed']:
    prefix = f'results/{identity}/'
    result = files[prefix + 'result.json']
    planned = plan[identity]
    config = result['config']
    assert all(config[key] == planned[key] for key in planned)
    assert config['candidate_commit'] == release['candidate_commit']
    assert config['base_commit'] == release['base']
    assert config['gpu_uuid'] == release['gpu_uuid']
    raw = files[prefix + 'output/speed_results.json']
    native, rows = raw['config'], raw['per_request']
    count = {'en': 1088, 'zh': 2020}[planned['language']]
    assert len(rows) == result['coverage'] == result['speaker_sim']['samples'] == count
    assert result['speed']['total_requests'] == result['speed']['completed_requests'] == count
    assert result['speed']['failed_requests'] == result['wer']['skipped'] == 0
    assert result['wer']['evaluated'] == count
    assert native['seed'] == planned['seed']
    assert native['concurrency'] == native['warmup'] == planned['concurrency']
    assert native['max_running_requests'] == native['cuda_graph_max_bs'] == 64
    assert native['max_new_tokens'] == 2048 and native['stream'] is False
    assert native['max_samples'] is None and native['sample_offset'] == 0
    assert all(row['is_success'] for row in rows)
    ids = [row['id'] for row in rows]
    assert len(set(ids)) == count
    reference_ids.setdefault(planned['language'], ids)
    assert ids == reference_ids[planned['language']]
    sim = files[prefix + 'speaker_similarity.json']
    assert [row['id'] for row in sim] == ids
    assert math.isclose(statistics.mean(row['similarity'] for row in sim), result['speaker_sim']['mean'], abs_tol=1e-12)
    hashes = files[prefix + 'audio_sha256.json']
    assert set(hashes) == set(ids) and all(len(value) == 64 for value in hashes.values())
    runtime = files[prefix + 'runtime.json']
    assert runtime['gpu_uuid'].removeprefix('GPU-') == release['gpu_uuid'].removeprefix('GPU-')
    assert runtime['import'].startswith('/workspace/sglang-omni/')
    versions.add(tuple(sorted(runtime['versions'].items())))
    resolved = files[prefix + 'resolved-pipeline.json']
    assert resolved['model_path'] == 'inclusionAI/Ming-3.0-tts-0.5B@8d66b70a00f05ad183fa8a863b4ce609fc83cbc0'
    costs = result['costs']
    start = next(row['epoch'] for row in costs['events'] if row['event'] == 'Starting server:')
    ready = next(row['epoch'] for row in costs['events'] if row['event'] == 'Service is ready.')
    stop = next(row['epoch'] for row in costs['events'] if row['event'] == 'Stopping server')
    assert math.isclose(ready - start, costs['startup_to_ready_s'], abs_tol=1e-9)
    graphs = files.get(prefix + 'graphs.jsonl', [])
    assert sum(start <= row['epoch'] <= stop for row in graphs) == costs['successful_tts_captures']
    memory = []
    for row in files[prefix + 'memory.json']:
        if start <= row['epoch'] <= stop:
            assert row['exit_code'] == 0
            for line in row['output'].splitlines():
                uuid, used = line.split(',')
                if uuid.strip() == release['gpu_uuid']:
                    memory.append(float(used))
    assert memory and math.isclose(max(memory) / 1024, costs['peak_tts_device_gib'])
    results[identity] = result
assert len(versions) <= 1
groups = {}
for row in plan.values():
    groups.setdefault(f"{row['comparison']}/{row['language']}-c{row['concurrency']}", []).append(row['id'])
cells, adverse = {}, []
for key, identities in groups.items():
    missing = [identity for identity in identities if identity not in results]
    cell = {'status': 'pending' if missing else 'complete', 'missing': missing}
    if not missing:
        records = [results[identity] for identity in identities]
        assert [row['config']['label'] for row in records] == ['A42', 'B42', 'B43', 'A43']
        finishes = [datetime.datetime.fromisoformat(row['finished_utc']) for row in records]
        assert all(a < b for a, b in zip(finishes, finishes[1:]))
        for arm in ['A', 'B']:
            paired = [row for row in records if row['config']['label'].startswith(arm)]
            cell[arm] = {
                'throughput_qps': statistics.mean(row['speed']['throughput_qps'] for row in paired),
                'latency_mean_s': statistics.mean(row['speed']['latency_mean_s'] for row in paired),
                'latency_p95_range_s': [min(row['speed']['latency_p95_s'] for row in paired), max(row['speed']['latency_p95_s'] for row in paired)],
                'wer': statistics.mean(row['wer']['wer_corpus'] for row in paired),
                'sim': statistics.mean(row['speaker_sim']['mean'] for row in paired),
                'attempted': sum(row['speed']['total_requests'] for row in paired),
                'failed': sum(row['speed']['failed_requests'] for row in paired),
                'output_tokens': sum(row['speed']['output_tokens_total'] for row in paired),
                'startup_s': statistics.mean(row['costs']['startup_to_ready_s'] for row in paired),
                'peak_tts_device_gib': max(row['costs']['peak_tts_device_gib'] for row in paired),
                'captures': sorted({row['costs']['successful_tts_captures'] for row in paired}),
            }
        for seed in [42, 43]:
            a = next(row for row in records if row['config']['label'] == f'A{seed}')
            b = next(row for row in records if row['config']['label'] == f'B{seed}')
            wer_delta = b['wer']['wer_corpus'] - a['wer']['wer_corpus']
            sim_delta = b['speaker_sim']['mean'] - a['speaker_sim']['mean']
            if wer_delta > 0 or sim_delta < 0:
                adverse.append({'cell': key, 'seed': seed, 'wer_delta': wer_delta, 'sim_delta': sim_delta})
    cells[key] = cell
geometric = {}
for comparison in sorted({row['comparison'] for row in plan.values()}):
    geometric[comparison] = {}
    for concurrency in [1, 16, 32, 64]:
        pair = [cells.get(f'{comparison}/{language}-c{concurrency}') for language in ['en', 'zh']]
        geometric[comparison][concurrency] = (
            100 * (math.sqrt(math.prod(row['B']['throughput_qps'] / row['A']['throughput_qps'] for row in pair)) - 1)
            if all(row and row['status'] == 'complete' for row in pair) else None
        )
summary = {'base': release['base'], 'candidate': release['candidate_commit'],
           'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'completed_arms': len(results), 'expected_arms': len(plan), 'cells': cells,
           'geometric_throughput_change_percent': geometric, 'per_seed_adverse_quality': adverse}
(root / 'current-matrix-summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({'completed_arms': len(results), 'complete_cells': [key for key, value in cells.items() if value['status'] == 'complete']}))
