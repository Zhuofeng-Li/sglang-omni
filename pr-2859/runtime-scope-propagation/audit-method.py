"""Independently audit fresh c64 data and explicitly attributed c1 reuse."""
import hashlib
import json
import math
import re
from pathlib import Path

import yaml

from audit_moss_stream_scope import audit as audit_previous


def load(path):
    return json.loads(path.read_text())


def audit(root):
    protocol_path = root / 'control/moss-runtime-scope-protocol.json'
    protocol = load(protocol_path)
    output = dict(status='pending_or_invalid', candidate=protocol['candidate'],
                  frozen_main=protocol['base'], generations=[], blocks=[])
    try:
        previous = audit_previous(root)
        assert previous['status'] == 'verified', previous
        assert previous['candidate'] == protocol['c1_reuse']['candidate']
        fresh = root / 'evidence' / protocol['namespace']
        reused = root / 'evidence' / protocol['c1_reuse']['namespace']
        state = load(fresh / 'control/validation-state.json')
        assert state['status'] == 'complete', state
        assert state['candidate'] == protocol['candidate']
        assert state['source_digest_sha256'] == protocol['source_digest_sha256']
        assert state['protocol_sha256'] == hashlib.sha256(protocol_path.read_bytes()).hexdigest()
        for name, expected in [('moss-regression', {'passed':375}),
                               ('cuda-hidden-regression', {'passed':278, 'skipped':97})]:
            assert (fresh / 'control' / (name + '.exit')).read_text().strip() == '0'
            log = (fresh / 'control' / (name + '.log')).read_text()
            summary = [line for line in log.splitlines() if re.search(r'\b\d+ passed\b', line)][-1]
            counts = {kind:int(count) for count,kind in re.findall(r'(\d+) (passed|skipped|failed|error|deselected|xfailed|xpassed)', summary)}
            assert counts == expected, (name, counts)
        old_scorer = load(reused / 'control/moss-scorer-identity.json')
        new_scorer = load(fresh / 'control/moss-scorer-identity.json')
        assert old_scorer['verified_unchanged_after_all_scores']
        assert new_scorer['verified_unchanged_after_all_scores']
        assert old_scorer['files'] == new_scorer['files']
        expected = {f'pr2859-c64-{m}-{a}-seed{s}' for m in ['stream','nonstream']
                    for a,s in [('main',42),('pr',42),('pr',43),('main',43)]}
        assert {p.name for p in (fresh / 'moss-results').iterdir()} == expected
        for concurrency in [1,64]:
            work = reused if concurrency == 1 else fresh
            actual_candidate = protocol['c1_reuse']['candidate'] if concurrency == 1 else protocol['candidate']
            for mode in ['nonstream','stream']:
                rows = []
                for arm,seed in [('main',42),('pr',42),('pr',43),('main',43)]:
                    name = f'pr2859-c{concurrency}-{mode}-{arm}-seed{seed}'
                    directory = work / 'moss-results' / name
                    result = load(directory / 'result.json')
                    assert result['exit_code'] == 0 and result['gpu_uuid'] == protocol['gpu_uuid']
                    assert (result['arm'],result['seed'],result['concurrency'],result['mode']) == (arm,seed,concurrency,mode)
                    assert result['source'] == f'/qualification/{work.name}/source/' + ('main' if arm == 'main' else 'pr-2859')
                    assert result['finished_at'] > result['started_at'] and result['peak_mib'] > 0
                    speed = load(directory / 'speed-summary.json')
                    assert speed['sample_count'] == speed['summary']['total_requests'] == speed['summary']['completed_requests'] == 1088
                    assert speed['summary']['failed_requests'] == 0
                    config = speed['config']
                    assert (config['concurrency'],config['stream'],config['seed']) == (concurrency,mode == 'stream',seed)
                    assert config['max_new_tokens'] == 2048 and config['warmup'] == 16
                    assert config['max_running_requests'] == config['cuda_graph_max_bs'] == 64
                    assert math.isfinite(speed['summary']['throughput_qps'])
                    quality = {}
                    for kind,metric in [('wer','wer_corpus'),('similarity','speaker_similarity_mean')]:
                        q = load(directory / (kind + '-summary.json'))
                        assert q['sample_count'] == q['summary']['total_samples'] == q['summary']['evaluated'] == 1088
                        assert q['summary']['skipped'] == 0 and math.isfinite(q['summary'][metric])
                        assert q['sample_order_sha256'] == speed['sample_order_sha256']
                        quality[kind] = q
                    if mode == 'stream':
                        assert speed['summary']['playback_continuity_requests'] + speed['summary']['playback_continuity_na_requests'] == 1088
                    cost = load(directory / 'cost-summary.json')
                    graph = load(directory / 'graph-summary.json')
                    assert cost['startup_seconds'] > 0 and cost['successful_captures'] > 0
                    assert graph['successful_captures'] == cost['successful_captures']
                    row = dict(name=name,status='verified',quality='verified',result=result,speed=speed,costs=cost,
                               measured_candidate=actual_candidate,measurement_namespace=work.name,
                               provenance='reused_unchanged_c1' if concurrency == 1 else 'fresh_current_head_c64',**quality)
                    output['generations'].append(row)
                    rows.append((row,yaml.safe_load((directory / 'config.yaml').read_text())))
                assert all(rows[i][0]['result']['finished_at'] < rows[i+1][0]['result']['started_at'] for i in range(3))
                for left,right in [(rows[0],rows[1]),(rows[3],rows[2])]:
                    assert left[0]['speed']['sample_order_sha256'] == right[0]['speed']['sample_order_sha256']
                    assert left[1] == right[1]
                    excluded = {'base_url','server_config'}
                    assert {k:v for k,v in left[0]['speed']['config'].items() if k not in excluded} == {k:v for k,v in right[0]['speed']['config'].items() if k not in excluded}
                output['blocks'].append(dict(concurrency=concurrency,mode=mode,status='verified',
                                             actual_candidate=actual_candidate,namespace=work.name))
        output.update(status='verified',new_generation_WER_SIM_cohorts=8,reused_c1_cohorts=8,
                      reuse_reason=protocol['c1_reuse']['reason'],scorer_files_unchanged=True,
                      note='Coverage verified; benefit, quality, costs, current-main compatibility and review are separate gates.')
    except (AssertionError,FileNotFoundError,KeyError,ValueError,IndexError) as error:
        output['error'] = repr(error)
    return output


if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    import fcntl
    with (root / 'control/sync.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_SH)
        result = audit(root)
        (root / 'followup-2859/runtime-final-audit.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k not in ['generations','blocks']}))
