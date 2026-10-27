"""Prepare (without pushing) a distinct current-main evidence record."""
from pathlib import Path
import hashlib
import json
import shutil
import tarfile

from render_pr import continuity, table
from summarize_streaming import summarize

root = Path(__file__).resolve().parent
destination = root / 'evidence-repo/evidence/ming3-streaming-review/current-main'
destination.mkdir(parents=True, exist_ok=True)
data, raw_reports, smokes, logs = {}, {}, {}, {}
with tarfile.open(root / 'current-on-demand.tar.gz', 'r:gz') as archive:
    for member in archive:
        path = Path(member.name)
        assert not path.is_absolute() and '..' not in path.parts
        if not member.isfile():
            continue
        payload = archive.extractfile(member).read()
        if path.suffix in ['.json', '.csv', '.jsonl', '.log', '.yaml']:
            target = destination / 'raw' / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        if member.name.startswith('metrics-dense/') and member.name.endswith('/speed_results.json'):
            raw_reports[str(path.parent)] = json.loads(payload)
            data[str(path.parent)] = summarize(raw_reports[str(path.parent)])
        if member.name in ['smoke-dense/http-results.json', 'smoke-tiny/http-results.json']:
            smokes[path.parts[0]] = json.loads(payload)
        if member.name == 'smoke-quality/quality-results.json':
            quality = json.loads(payload)
        if member.name == 'stream-status.json':
            state = json.loads(payload)
        if member.name == 'test-status.json':
            tests = json.loads(payload)
        if member.name.startswith('unit-') and path.suffix == '.log':
            logs[path.name] = payload.decode()

assert state['stage'] == 'complete', state
assert state['source'] == '348f6973d4878ed77a9c6c60d072c91addaf15d8'
assert tests['stage'] == 'passed' and len(tests['completed']) == 3
assert len(data) == 16
reference_ids = {}
for language in ['en', 'zh']:
    for concurrency in [1, 32]:
        for mode in ['nonstream', 'stream']:
            for seed in [42, 43]:
                key = f'metrics-dense/{language}-c{concurrency}-{mode}-s{seed}'
                report = raw_reports[key]
                config, rows = report['config'], report['per_request']
                assert config['seed'] == seed and config['concurrency'] == concurrency
                assert config['warmup'] == concurrency
                assert config['stream'] == (mode == 'stream')
                assert config['max_running_requests'] == config['cuda_graph_max_bs'] == 32
                assert config['voice_clone'] and not config['no_ref_text']
                assert len(rows) == 128 and all(row['is_success'] for row in rows)
                ids = [row['id'] for row in rows]
                assert len(set(ids)) == 128
                if language not in reference_ids:
                    reference_ids[language] = ids
                assert ids == reference_ids[language]
                if mode == 'stream':
                    assert all(row['audio_ttfp_s'] is not None for row in rows)
                    assert all((row['max_playback_underrun_s'] is None) == (row['audio_chunk_count'] < 2) for row in rows)
assert quality['stage'] == 'complete' and len(quality['cases']) == 8
assert all(case['same_normalized_transcript'] for case in quality['cases'])
for smoke in smokes.values():
    assert smoke['stage'] == 'complete' and len(smoke['cases']) == 14
    assert smoke['disconnect_after_first_chunk'] and smoke['sse']['terminal']['finish_reason'] in ['stop', 'length']
    assert all(pair['offline_samples'] == pair['stream_samples'] for pair in smoke['comparisons'])

receipt = {
    'base': '0fe60cf6c102caf982430e1764243c6e5c749d76', 'stream_commit': state['source'],
    'completed_blocks': len(data), 'attempted': sum(row['attempted'] for row in data.values()),
    'failed': sum(row['failed'] for row in data.values()),
    'stream_requests': sum(row['attempted'] for key, row in data.items() if '-stream-' in key),
    'underrun_na': sum(row['continuity_na'] for key, row in data.items() if '-stream-' in key),
    'same_ordered_request_ids': True, 'http_smokes': {key: len(value['cases']) for key, value in smokes.items()},
    'paired_asr_cases': len(quality['cases']), 'all_paired_normalized_transcripts_match': True,
    'archive_sha256': hashlib.sha256((root / 'current-on-demand.tar.gz').read_bytes()).hexdigest(),
}
(root / 'current-summary.json').write_text(json.dumps(data, indent=2) + '\n')
(root / 'current-validation-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
for name in ['current-summary.json', 'current-validation-receipt.json', 'current-source-receipts.json',
             'current-source-plan.json', 'current-operator-hashes.json', 'current_stream.py',
             'measure.py', 'validate_integration.py', 'validate_quality.py', 'publish_current_evidence.py']:
    shutil.copyfile(root / name, destination / name)
lines = ['# Current-main Ming3 streaming validation', '',
         'Base: `0fe60cf6c102caf982430e1764243c6e5c749d76`; measured integration: `348f6973d4878ed77a9c6c60d072c91addaf15d8`.', '',
         'This is a fresh 0.5B mode comparison on the merged current-main implementation, not an isolated speedup over main. The original Tiny timing data in the parent report retain their original source and date. Tiny preprocessing remains concurrency one and does not use the changed bounded worker pool; both models received fresh HTTP and paired transcription checks here.', '',
         'Protocol matches the parent report: one H200, automatic config, 128 EN/ZH reference-conditioned requests, seeds 42/43, nonstream42 → stream42 → stream43 → nonstream43 per cell, c1/c32, server limits 32, native warmup equal to concurrency. One service spans all 16 dense blocks. Dense reference cache is seed-keyed and persists; stream42 can reuse nonstream42 while stream43 first introduces seed43. This is neither cold-reference latency nor a cache-normalized performance gain. Means are arithmetic seed means; p95 is the range of the two seed values.', '',
         '### Non-streaming', '', table(data, 'dense', 'nonstream'), '',
         '### Streaming', '', table(data, 'dense', 'stream'), '', continuity(data, 'dense'), '',
         'Playback begins immediately at the first nonempty packet, without added buffering. Underrun is the maximum late playback deadline per request; one-packet responses are N/A and excluded. Raw exported time resolution is 0.1 ms.', '',
         '### Functional checks', '',
         '| Model / case | Full WER or CER | Stream WER or CER | Same normalized transcript |',
         '| --- | ---: | ---: | --- |']
for case in quality['cases']:
    outputs = case['outputs']
    lines.append(f"| {case['model']} / {case['language']} / reference={case['reference']} | {100*outputs['offline']['wer_or_cer']:.2f}% | {100*outputs['stream']['wer_or_cer']:.2f}% | {case['same_normalized_transcript']} |")
lines += ['', 'Each model passed 14 PCM cases plus SSE and disconnect recovery. Matching ASR transcripts are a small functional check, not full-corpus quality qualification.', '',
          'Pinned H200 test suites, including Ming3/Ming-TTS, MPS, CPU-locality, shared scheduler and stage environment: candidate `3f8593f` 386 passed; integrated stream `348f697` 402 passed; Tiny performance `ea0958c` 411 passed and 6 skipped. Full logs and source receipts are under `raw/`.', '']
(destination / 'report.md').write_text('\n'.join(lines))
manifest = {str(path.relative_to(destination)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in destination.rglob('*') if path.is_file() and path.name != 'sha256.json'}
(destination / 'sha256.json').write_text(json.dumps(manifest, indent=2) + '\n')
parent = destination.parent
report_path = parent / 'report.md'
report = report_path.read_text()
notice = ('\n**Current-main follow-up:** the [fresh 0.5B measurement and both-model integration checks]'
          '(current-main/report.md) use main `0fe60cf6` and integration `348f6973`. '
          'The tables below remain the original measurements; Tiny timings retain that original source.\n')
if notice not in report:
    report = report.replace('# Ming3 streaming review evidence\n', '# Ming3 streaming review evidence\n' + notice, 1)
report = report.replace('Current heads `f24ba6fa`', 'Then-published heads `f24ba6fa`')
report_path.write_text(report)
manifest = {str(path.relative_to(parent)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in parent.rglob('*') if path.is_file() and path != parent / 'sha256.json'}
(parent / 'sha256.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(receipt))
