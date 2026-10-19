from pathlib import Path
import collections,datetime,hashlib,json,math,shutil
import yaml
R=Path(__file__).resolve().parents[1]
SHARED=Path('/scratch/user/zhuofengli_tamu.edu/tasks/omni-review-fixes/runs/20261019/evidence')
CONTROL=SHARED/'remote-control'
receipt_path=CONTROL/'pr2881-h100-audit-complete.json'
if not receipt_path.exists():
    print('Pending H100 completion receipt in persistent evidence.');raise SystemExit(2)
receipt=json.loads(receipt_path.read_text())
assert receipt['status']=='complete' and receipt['cohorts']==receipt['measured_cohorts']==24 and receipt['language_pairs']==24
for name,digest in receipt['files_sha256'].items():
    assert hashlib.sha256((CONTROL/name).read_bytes()).hexdigest()==digest
state=json.loads((CONTROL/'review-2881-priority-state.json').read_text())
assert state['status']=='complete' and len(state['cases'])==24
expected=[]
for mode in ['nonstream','stream']:
    for arm,seed in [('async_only',42),('scoped_admission',42),('scoped_admission',43),('async_only',43)]:
        expected.append(f'pr2881-c32-{mode}-{arm}-seed{seed}-async-admission-ablation')
for c in [32,64]:
    for mode in ['nonstream','stream']:
        for arm,rep in [('main',1),('pr',1),('pr',2),('main',2)]:
            expected.append(f'pr2881-c{c}-{mode}-{arm}-seed42-fixed-seed42-repeat{rep}')
assert [c['name'] for c in state['cases']]==expected
out=R/'h100-evidence';(out/'control').mkdir(parents=True,exist_ok=True)
for name in [*receipt['files_sha256'],'pr2881-h100-audit-complete.json','review-2881-priority-state.json','async-only-variant.patch','software-identity.json','assets-identity.json']:
    shutil.copy2(CONTROL/name,out/'control'/name)
assert hashlib.sha256((out/'control/async-only-variant.patch').read_bytes()).hexdigest()==state['async_only_variant']['patch_sha256']
intervals=[];results={};total=0;costs={}
for case in state['cases']:
    source=SHARED/'results'/case['name'];dest=out/'results'/case['name'];dest.mkdir(parents=True,exist_ok=True)
    names=['result.json','launch.json','config.yaml','en-warmup-summary.json','zh-warmup-summary.json','memory-samples.json']
    missing=[n for n in names if not (source/n).exists()]
    if missing:
        print('Pending evidence sync:',case['name'],missing);raise SystemExit(2)
    for name in names:shutil.copy2(source/name,dest/name)
    data=json.loads((dest/'result.json').read_text());launch=json.loads((dest/'launch.json').read_text())
    assert data['status']=='completed' and launch['seed']==case['seed']
    config=yaml.safe_load((dest/'config.yaml').read_text());assert config==launch['config']
    assert config['stages']['asr']['engine']=={'disable_radix_cache':True,'random_seed':case['seed']}
    assert config['stages']['asr']['factory']=={'dtype':'bfloat16','pre_lm_cache_size_bytes':1,'mm_embedding_cache_size_bytes':0}
    assert launch['source']=='/qualification/source/'+case['source']
    for lang,count in [('en',1088),('zh',2020)]:
        measured=data['measurements'][lang]['summary'];warm=json.loads((dest/f'{lang}-warmup-summary.json').read_text())['summary']
        assert measured['evaluated']==measured['total_samples']==count and measured['skipped']==0
        assert warm['evaluated']==count and warm['skipped']==0
        assert math.isfinite(measured['wer_corpus']);total+=count
    samples=json.loads((dest/'memory-samples.json').read_text());assert samples
    assert all(x['gpu']=='GPU-e9f60c1d-8856-043c-42cd-47a942a4d8f1' for x in samples)
    assert max(x['memory_mib'] for x in samples)==data['peak_memory_mib']
    assert data['startup_seconds']>0 and data['peak_memory_mib']>0
    assert data['graphs_after_scoring']['successful_captures']>=data['graphs_after_scoring']['live_captures']>0
    intervals.append({'name':case['name'],'first_sample':samples[0]['time'],'last_sample':samples[-1]['time']})
    results[case['name']]=data
    group='admission' if case['label']=='async-admission-ablation' else 'repeats'
    costs.setdefault(group,{}).setdefault(case['arm'],[]).append({'startup_s':data['startup_seconds'],'peak_gib':data['peak_memory_mib']/1024,'successful':data['graphs_after_scoring']['successful_captures'],'live':data['graphs_after_scoring']['live_captures']})
assert all(a['last_sample']<b['first_sample'] for a,b in zip(intervals,intervals[1:]))
summary=json.loads((CONTROL/'pr2881-h100-priority-summary.json').read_text())
assert summary['head']=='e98bcf05e6d27d877cfb134900900ca6fad5d76a' and summary['base']=='2d5de98cd92b17df7974ac2ef4192b4a99263845'
assert len(summary['rows'])==24 and len(summary['groups'])==6
for row in summary['rows']:
    left,right=[results[row[k]]['measurements'][row['lang']] for k in ['left_source_result','right_source_result']]
    assert left['sample_order_sha256']==right['sample_order_sha256']
    for key,value in [('left',left),('right',right)]:
        assert row[key]['req_s']==value['speed']['throughput_samples_per_s']
        assert row[key]['wer_percent']==value['summary']['wer_corpus']*100
        assert row[key]['failed']==0
for group in summary['groups']:
    ratios=[]
    for lang in ['en','zh']:
        cells=[r for r in summary['rows'] if r['kind'].startswith(group['kind']) and r['c']==group['concurrency'] and r['mode']==group['mode'] and r['lang']==lang]
        assert len(cells)==2
        ratios.append(sum(r['right']['req_s'] for r in cells)/sum(r['left']['req_s'] for r in cells))
    assert math.isclose(group['geometric_throughput_change_percent'],100*(math.sqrt(math.prod(ratios))-1),abs_tol=1e-10)
assert total==74592
audit={'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'head':summary['head'],'base':summary['base'],'source_identity':'h100-identity-at-start.json','cohorts':24,'scored_requests':total,'failed':0,'warmup_full_split_verified':True,'memory_sampling_same_original_GPU_verified':True,'six_ABBA_groups_in_declared_order_verified':True,'paired_sample_orders_and_aggregates_verified':True,'intervals':intervals,'costs':costs,'coverage':'complete original-card review qualification','readiness':'Decide from all retained latency/quality results and independent review; complete coverage does not imply readiness.'}
(R/'h100-evidence-audit.json').write_text(json.dumps(audit,indent=2))
print(json.dumps({'cohorts':24,'scored_requests':total,'failed':0,'warmup_verified':True,'ABBA_and_GPU_verified':True,'destination':str(out)}))
