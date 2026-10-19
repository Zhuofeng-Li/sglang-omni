import fcntl, json, subprocess, time
from pathlib import Path
r=Path(__file__).resolve().parents[1]
lock=(r/'control/sync.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX)
ssh=str(r/'control/ssh');node='/data/zhuofeng-li/home/omni-review-20261019'
subprocess.run([ssh, 'python3 '+node+'/control/export_minimal.py'],check=True)
for remote,local,include in [
 ('control','remote-control',['*.log','*.exit','*-state.json','*-status.json','quality-differences.json','async-only-variant.patch','assets-identity.json','source-identity.json','software-identity.json','moss-scorer-identity.json','moss-ablation-protocol.json','moss-ablation-verification.json']),
 ('results','results',['result.json','status.json','launch.json','config.yaml','*-warmup-summary.json','memory-samples.json','graphs-*.jsonl']),
 ('moss-results','moss-results',['result.json','speed-summary.json','wer-summary.json','similarity-summary.json','graph-summary.json','cost-summary.json','config.yaml','failed-attempt-*.json','failed-attempt-*.log']),
 ('moss-ablation-results','moss-ablation-results',['result.json','speed-summary.json','wer-summary.json','similarity-summary.json','graph-summary.json','cost-summary.json','config.yaml']),
]:
 destination=r/'evidence'/local;destination.mkdir(parents=True,exist_ok=True)
 cmd=['rsync','-a','--prune-empty-dirs','-e',ssh,'--include=*/']
 cmd+=['--include='+name for name in include]+['--exclude=*','ignored:'+node+'/'+remote+'/',str(destination)+'/']
 subprocess.run(cmd,check=True)
rows=[]
for p in (r/'evidence/results').glob('*/status.json'):
 d=json.loads(p.read_text());rows.append({k:d.get(k) for k in ['name','status','error']})
(r/'sync-status.json').write_text(json.dumps({'at':time.time(),'rows':rows},indent=2))
print(json.dumps({'saved_cohorts':len(rows),'complete':sum(x['status']=='completed' for x in rows)}))
