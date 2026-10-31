from pathlib import Path
import datetime
import hashlib
import json
import math
import re
import statistics
import sys
import tarfile
import time

root = Path(__file__).resolve().parent
archive_path = Path(sys.argv[1]) if len(sys.argv) > 1 else root / 'latest-results.tar.gz'
payload = archive_path.read_bytes()
pending_arm = sys.argv[2] if len(sys.argv) > 2 else None
plan = {row['id']: row for row in json.loads((root / 'measurement-plan.json').read_text())}
sources = json.loads((root / 'source-manifest.json').read_text())
checked = []
runtime_identity = None
with tarfile.open(archive_path) as archive:
    def read(name):
        return json.load(archive.extractfile(name))
    queue = read('queue-status.json')
    assert queue['completed'] == list(plan)[:len(queue['completed'])], 'Completed arms must preserve the predeclared order'
    audit_arms = list(queue['completed'])
    if pending_arm:
        assert pending_arm == queue['active'] == list(plan)[len(audit_arms)]
        hold = json.loads((root / 'resource-auth-hold-observation.json').read_text())
        assert hold['active'] == pending_arm and hold['full_result_ready'] and hold['queue_parent_state'] == 'T'
        audit_arms.append(pending_arm)
    for arm in audit_arms:
        prefix = 'results/' + arm + '/'
        result = read(prefix + 'result.json')
        speed = read(prefix + 'output/speed_results.json')
        quality = read(prefix + 'output/wer_results.json')
        similarity = read(prefix + 'speaker_similarity.json')
        hashes = read(prefix + 'audio_sha256.json')
        config = read(prefix + 'config.json')
        assert result['config'] == config
        assert result['speed'] == speed['summary']
        assert result['wer'] == quality['summary']
        runtime = read(prefix + 'runtime.json')
        assert runtime['gpu_uuid'].removeprefix('GPU-').lower() == config['gpu_uuid'].removeprefix('GPU-').lower()
        assert runtime['import'].startswith('/workspace/sglang-omni/')
        if runtime_identity is None:
            runtime_identity = runtime
        else:
            assert runtime == runtime_identity, (arm, 'runtime or CPU affinity differs')
        assert config == plan[arm]
        resolved = read(prefix + 'resolved-pipeline.json')
        assert resolved['mps'] == 'off', (arm, 'Default-off qualification unexpectedly enabled MPS')
        count = {'en': 1088, 'zh': 2020}[config['language']]
        requests = speed['per_request']
        ids = [row['id'] for row in requests]
        assert len(ids) == len(set(ids)) == result['coverage'] == count
        assert all(row['is_success'] and not row['error'] for row in requests)
        assert speed['summary']['completed_requests'] == speed['summary']['total_requests'] == count
        assert speed['summary']['failed_requests'] == 0
        finish_reasons = {reason: sum(row['finish_reason'] == reason for row in requests) for reason in ['stop', 'length', 'unknown']}
        assert sum(finish_reasons.values()) == count
        assert speed['summary']['finish_reason_observed'] == count - finish_reasons['unknown']
        assert speed['summary']['max_token_hits'] == finish_reasons['length']
        assert speed['config']['stream'] == config['stream']
        assert speed['config']['concurrency'] == config['concurrency']
        assert speed['config']['seed'] == config['seed']
        assert all(math.isfinite(row['latency_s']) and row['latency_s'] > 0 and row['audio_duration_s'] > 0 for row in requests)
        if config['stream']:
            assert all(row['audio_ttfp_s'] is not None and 0 < row['audio_ttfp_s'] <= row['latency_s'] + 0.0002 and row['audio_chunk_count'] >= 1 and row['first_audio_payload_bytes'] > 0 for row in requests), (arm, 'Missing or invalid streaming first-packet evidence')
            assert math.isclose(statistics.mean(row['audio_ttfp_s'] for row in requests), speed['summary']['audio_ttfp_mean_s'], abs_tol=0.00011)
        samples = quality['per_sample']
        assert len(samples) == count and {row['id'] for row in samples} == set(ids)
        assert all(row['is_success'] and not row['error'] for row in samples)
        edits = sum(row['substitutions'] + row['deletions'] + row['insertions'] for row in samples)
        units = sum(row['substitutions'] + row['deletions'] + row['hits'] for row in samples)
        assert units > 0 and math.isclose(edits / units, quality['summary']['wer_corpus'], rel_tol=1e-10)
        assert quality['summary']['evaluated'] == count and quality['summary']['skipped'] == 0
        assert len(similarity) == count and {row['id'] for row in similarity} == set(ids)
        assert all(math.isfinite(row['similarity']) and -1.000001 <= row['similarity'] <= 1.000001 for row in similarity)
        sim_mean = statistics.mean(row['similarity'] for row in similarity)
        assert math.isclose(sim_mean, result['speaker_sim']['mean'], rel_tol=1e-9)
        assert set(hashes) == set(ids) and all(len(value) == 64 for value in hashes.values())
        assert math.isclose(statistics.mean(row['latency_s'] for row in requests), speed['summary']['latency_mean_s'], abs_tol=0.00051)
        log = archive.extractfile(prefix + 'benchmark.log').read().decode(errors='replace')
        events = []
        for line in log.splitlines():
            match = re.search(r'(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d+) .*?(Starting server:|Service is ready\.|Stopping server)', line)
            if match:
                stamp = datetime.datetime.strptime(match[1], '%Y-%m-%d %H:%M:%S,%f').replace(tzinfo=datetime.timezone.utc).timestamp()
                events.append((stamp, match[2]))
        start = next(stamp for stamp, event in events if event == 'Starting server:')
        ready = next(stamp for stamp, event in events if stamp >= start and event == 'Service is ready.')
        stop = next(stamp for stamp, event in events if stamp >= start and event == 'Stopping server')
        assert math.isclose(ready - start, result['costs']['startup_to_ready_s'], abs_tol=1e-6)
        finished = datetime.datetime.fromisoformat(result['finished_utc']).timestamp()
        assert start < ready < stop < finished
        if checked:
            assert checked[-1]['full_quality_finished_epoch'] <= start, (arm, 'Measurement arms overlap or violate actual execution order')
        captures = [json.loads(line) for line in archive.extractfile(prefix + 'graphs.jsonl').read().splitlines()]
        capture_count = sum(start <= event['epoch'] <= stop for event in captures)
        assert capture_count == result['costs']['successful_tts_captures']
        memory = read(prefix + 'memory.json')
        points = []
        for sample in memory:
            if start <= sample['epoch'] <= stop and sample['exit_code'] == 0:
                for line in sample['output'].splitlines():
                    gpu, used = line.split(',')
                    if gpu.strip() == config['gpu_uuid']:
                        points.append((sample['epoch'], float(used)))
        assert points and math.isclose(max(used for _, used in points) / 1024, result['costs']['peak_tts_device_gib'], abs_tol=1e-9)
        gaps = [later[0] - earlier[0] for earlier, later in zip(points, points[1:])]
        checked.append({'arm': arm, 'requests': count, 'failed': 0, 'quality_evaluated': count,
                        'edits': edits, 'reference_units': units, 'wer_percent': 100 * edits / units,
                        'sim_mean': sim_mean, 'throughput_qps_reported': speed['summary']['throughput_qps'],
                        'actual_source_commit': sources[{'control': 'main', 'candidate3136': '3136', 'integrated-final': '3190'}[config['arm']]]['commit'],
                        'paired_candidate_identifier': config['candidate_commit'],
                        'resolved_mps': resolved['mps'],
                        'finish_reasons': finish_reasons,
                        'finish_reason_observed': count - finish_reasons['unknown'],
                        'tts_start_epoch': start, 'tts_ready_epoch': ready, 'tts_stop_epoch': stop,
                        'full_quality_finished_epoch': finished,
                        'stream_first_packet_coverage': count if config['stream'] else None,
                        'costs_verified_from_raw_logs': True,
                        'capture_end_events_during_tts': capture_count,
                        'memory_points_during_tts': len(points),
                        'memory_poll_gap_median_s': statistics.median(gaps) if gaps else None,
                        'memory_poll_gap_max_s': max(gaps) if gaps else None,
                        'memory_poll_failures': sum(sample['exit_code'] != 0 for sample in memory),
                        'verification': 'Unique matching request/quality/SIM/audio-hash IDs, completion, errors and score arithmetic checked.'})
output = {'verified_epoch': time.time(), 'source_archive_sha256': hashlib.sha256(payload).hexdigest(),
          'runtime_identity_equal_across_completed_arms': True,
          'runtime_versions': runtime_identity['versions'] if runtime_identity else None,
          'checked': checked, 'completed_count': len(queue['completed']), 'checked_count': len(checked),
          'pending_queue_ack_audit': pending_arm, 'authoritative_queue_state_unchanged': True, 'expected_count': len(plan),
          'limitations': ['Native throughput summary is preserved; reports lack absolute per-request start/end times to independently recompute throughput.',
                         'Memory is the maximum observed device usage under nominal one-second polling; actual sampling gaps are retained. Capture counts are successful capture_end events, not necessarily unique graphs.',
                         'Artifact checks are not an independent experiment rerun; uncompleted paired cells have no conclusion.']}
(root / ('pending-arm-verification.json' if pending_arm else 'completed-arm-verification.json')).write_text(json.dumps(output, indent=2) + '\n')
print(json.dumps(output))
