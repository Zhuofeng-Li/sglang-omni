from pathlib import Path
import json,collections,statistics,datetime
r=Path(__file__).resolve().parents[1]
state=json.loads((r/'evidence/control/review-backfill-state.json').read_text())
diffs=json.loads((r/'evidence/control/transcript-differences.json').read_text())
assert len(state['cases'])==28
counts={};unique=set()
for pair in diffs:
    kind='admission_ablation' if pair['kind']=='admission-ablation' else 'main_pr_repeats'
    count=counts.setdefault(kind,collections.Counter())
    for item in pair['changes']:
        count['changed']+=1
        count['better' if item['right_wer']<item['left_wer'] else 'worse' if item['right_wer']>item['left_wer'] else 'equal']+=1
        count['empty_right']+=int(not item['right']);count['empty_left']+=int(not item['left'])
        unique.add((item['reference'],item['left'],item['right']))
costs={};total=0
for case in state['cases']:
    folder=r/'evidence/results'/case['name']
    data=json.loads((folder/'result.json').read_text());launch=json.loads((folder/'launch.json').read_text())
    assert data['status']=='completed'
    assert launch['seed']==case['seed'] and launch['config']['stages']['asr']['engine']['random_seed']==case['seed']
    assert launch['config']['stages']['asr']['engine']['disable_radix_cache']
    assert launch['config']['stages']['asr']['factory']=={'dtype':'bfloat16','pre_lm_cache_size_bytes':1,'mm_embedding_cache_size_bytes':0}
    for lang,n in [('en',8 if case['smoke'] else 1088),('zh',8 if case['smoke'] else 2020)]:
        metrics=data['measurements'][lang]
        assert metrics['summary']['evaluated']==n and metrics['summary']['skipped']==0
        if not case['smoke']:total+=n
    if case['smoke']:continue
    group='admission_ablation' if case['label']=='async-admission-ablation' else 'main_pr_repeats'
    costs.setdefault(group,{}).setdefault(case['arm'],[]).append({'startup':data['startup_seconds'],'peak_gib':data['peak_memory_mib']/1024,'successful':data['graphs_after_scoring']['successful_captures'],'live':data['graphs_after_scoring']['live_captures']})
cost_summary={group:{arm:{'cohorts':len(items),'startup_mean_seconds':statistics.mean(x['startup'] for x in items),'startup_range_seconds':[min(x['startup'] for x in items),max(x['startup'] for x in items)],'peak_max_gib':max(x['peak_gib'] for x in items),'successful_captures':sorted(set(x['successful'] for x in items)),'live_captures':sorted(set(x['live'] for x in items))} for arm,items in arms.items()} for group,arms in costs.items()}
assessment={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_head':'e98bcf05e6d27d877cfb134900900ca6fad5d76a','measured_base':'2d5de98cd92b17df7974ac2ef4192b4a99263845','hardware':'H200 supplementary; original H100 confirmation still pending','formal_cohorts':24,'smoke_cohorts':4,'formal_scored_requests':total,'failed':0,'paired_language_cells':24,'transcript_changes':counts,'distinct_changed_triples_inspected':len(unique),'inspection':'Inspected all 31 distinct normalized reference/left/right triples. Names, homophones, singular/plural alternatives and short added/omitted particles; both improved and worsened WER. No changed hypothesis is empty. This does not establish numerical cause or rule out truncation.','costs':cost_summary,'readiness':'Not merge-ready: first-text latency increases persist; C64 streaming EN P95 worsens in one H200 repeat and improves in the other, so the original H100 regression cannot be dismissed. Admission-only streaming throughput change is near zero/negative. Await original H100 confirmation and independent reviewer approval.'}
(r/'supplement-assessment.json').write_text(json.dumps(assessment,ensure_ascii=False,indent=2))
p=r/'manifest.json';manifest=json.loads(p.read_text());manifest.update(status='complete_saved_released',formal_completed=24,formal_expected=24,updated_at_utc=assessment['at_utc'],release_verified_at_utc=json.loads((r/'monitor-state.json').read_text())['at_utc']);p.write_text(json.dumps(manifest,indent=2))
print(json.dumps(assessment,ensure_ascii=False,indent=2))
