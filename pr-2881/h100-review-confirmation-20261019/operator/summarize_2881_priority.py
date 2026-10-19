import json, os, hashlib, math, time
from pathlib import Path
R=Path(os.environ.get('QUAL_ROOT','/qualification'))
state=json.loads((R/'control/review-2881-priority-state.json').read_text())
assert state['status']=='complete' and len(state['cases'])==24
rows=[]; diffs=[]
for mode in ['nonstream','stream']:
 pairs=[]
 for seed in [42,43]:
  prefix=f'pr2881-c32-{mode}'
  pairs.append(('admission-ablation',32,seed,f'{prefix}-async_only-seed{seed}-async-admission-ablation',f'{prefix}-scoped_admission-seed{seed}-async-admission-ablation'))
 for c in [32,64]:
  for rep in [1,2]:
   prefix=f'pr2881-c{c}-{mode}';suffix=f'-seed42-fixed-seed42-repeat{rep}'
   pairs.append((f'fixed-seed-repeat{rep}',c,42,f'{prefix}-main{suffix}',f'{prefix}-pr{suffix}'))
 for kind,c,seed,leftname,rightname in pairs:
  left=json.loads((R/'results'/leftname/'result.json').read_text()); right=json.loads((R/'results'/rightname/'result.json').read_text())
  assert left['status']==right['status']=='completed'
  for d in [left,right]:
   assert d['startup_seconds']>0 and d['peak_memory_mib']>0
   assert d['graphs_after_scoring']['successful_captures']>0
  for lang,count in [('en',1088),('zh',2020)]:
   a,b=[d['measurements'][lang] for d in [left,right]]
   assert a['sample_order_sha256']==b['sample_order_sha256']
   for d in [a,b]:
    assert d['summary']['evaluated']==count and d['summary']['skipped']==0
   metric=lambda d:{'req_s':d['speed']['throughput_samples_per_s'],'latency_mean_ms':d['speed']['latency_mean_s']*1000,'latency_p95_ms':d['speed']['latency_p95_s']*1000,'ttft_mean_ms':None if 'text_ttft_mean_s' not in d['speed'] else d['speed']['text_ttft_mean_s']*1000,'ttft_p95_ms':None if 'text_ttft_p95_s' not in d['speed'] else d['speed']['text_ttft_p95_s']*1000,'wer_percent':d['summary']['wer_corpus']*100,'failed':d['summary']['skipped'],'attempted':d['summary']['total_samples']}
   am,bm=metric(a),metric(b)
   rows.append({'kind':kind,'c':c,'mode':mode,'seed':seed,'lang':lang,'left':am,'right':bm,'req_s_delta_percent':(bm['req_s']/am['req_s']-1)*100,'left_source_result':leftname,'right_source_result':rightname,'costs':[{k:d.get(k) for k in ['startup_seconds','peak_memory_mib','graphs_after_scoring']} for d in [left,right]]})
   raw=[json.loads((R/'results'/name/f'{lang}-raw.json').read_text()) for name in [leftname,rightname]]
   maps=[{x['id']:x for x in d['per_sample']} for d in raw]
   assert maps[0].keys()==maps[1].keys()
   changes=[]
   for sid,x in maps[0].items():
    y=maps[1][sid];assert x['ref_norm']==y['ref_norm']
    if x['hyp_norm']!=y['hyp_norm']:
     changes.append({'id':sid,'reference':x['ref_norm'],'left':x['hyp_norm'],'right':y['hyp_norm'],'left_wer':x['wer'],'right_wer':y['wer']})
   diffs.append({'kind':kind,'c':c,'mode':mode,'seed':seed,'lang':lang,'changes':changes})
assert len(rows)==24
summary={'scope':'Original-card H100 paired admission ablation and fixed-seed confirmation','base':'2d5de98cd92b17df7974ac2ef4192b4a99263845','head':'e98bcf05e6d27d877cfb134900900ca6fad5d76a','rows':rows}
groups=[]
for kind,concurrencies in [('admission-ablation',[32]),('fixed-seed-repeat',[32,64])]:
 for c in concurrencies:
  for mode in ['nonstream','stream']:
   ratios=[];languages={}
   for lang in ['en','zh']:
    cells=[x for x in rows if x['kind'].startswith(kind) and x['c']==c and x['mode']==mode and x['lang']==lang]
    assert len(cells)==2
    means={arm:sum(x[arm]['req_s'] for x in cells)/2 for arm in ['left','right']}
    ratios.append(means['right']/means['left'])
    languages[lang]={'req_s_arithmetic_mean':means,'per_pair_metrics':[{arm:x[arm] for arm in ['left','right']} for x in cells]}
   groups.append({'kind':kind,'concurrency':c,'mode':mode,'geometric_throughput_change_percent':100*(math.sqrt(math.prod(ratios))-1),'languages':languages})
summary['groups']=groups
summary['aggregation']='For each matched block, average req/s across the two seeds/repetitions within each arm/language, then take the geometric mean of the two language ratios; percentile and WER values remain per pass.'
digests={}
for name,value in [('pr2881-h100-priority-summary.json',summary),('pr2881-h100-transcript-differences.json',diffs)]:
 payload=json.dumps(value,ensure_ascii=False,indent=2)
 target=R/'control'/name;temporary=target.with_suffix('.partial')
 temporary.write_text(payload);temporary.replace(target)
 digests[name]=hashlib.sha256(target.read_bytes()).hexdigest()
receipt={'status':'complete','at':time.time(),'cohorts':24,'measured_cohorts':24,'language_pairs':24,'files_sha256':digests}
target=R/'control/pr2881-h100-audit-complete.json';temporary=target.with_suffix('.partial')
temporary.write_text(json.dumps(receipt,indent=2));temporary.replace(target)
print('Verified 24 measured cohorts, 24 language-pairs, no additional smoke cohorts')
