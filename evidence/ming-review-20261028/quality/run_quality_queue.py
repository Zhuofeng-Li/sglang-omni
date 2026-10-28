from pathlib import Path
import datetime,json,subprocess,time,os
root=Path(__file__).resolve().parent
state_path=root/'quality-queue-status.json'
if state_path.exists():raise RuntimeError('Existing queue state; inspect before resuming')
assert json.loads((root/'unit-status.json').read_text())['stage']=='passed'
assert '"en": 1088' in (root/'warm-dataset.log').read_text()
assert json.loads((root/'assets-status.json').read_text())['stage']=='complete'
plan=[]
for language,concurrency in [('en',16),('zh',1)]:
 for label,arm,seed in [('A42','corrected-main',42),('B42','candidate3136',42),('B43','candidate3136',43),('A43','corrected-main',43),('repeat-A42','corrected-main',42),('repeat-A43','corrected-main',43)]:
  plan.append({'id':f'quality-{language}-c{concurrency}-{label}','language':language,'concurrency':concurrency,'label':label,'arm':arm,'seed':seed,'variant':'native','candidate_commit':'3f8593f4cae19fe1c71e929a854bdc03b2c185e6','base_commit':'0fe60cf6c102caf982430e1764243c6e5c749d76','corrected_control_commit':'0d6a414e5e15c996900620d263143c89e0dd8acd','gpu_uuid':'GPU-99e2ecd1-862a-4af1-222d-841708198f30'})
(root/'quality-plan.json').write_text(json.dumps(plan,indent=2))
state={'stage':'starting','completed':[],'expected':len(plan),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
def save():
 state['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();p=root/'quality-status.partial';p.write_text(json.dumps(state,indent=2));p.replace(state_path)
save()
try:
 for cell in plan:
  if time.time()>1793241073-1800:raise RuntimeError('Lease close to expiry; preserve results and extend only after ownership check')
  output=root/'quality-results'/cell['id'];output.mkdir(parents=True,exist_ok=False);(output/'config.json').write_text(json.dumps(cell,indent=2));state.update(stage='running',active=cell['id']);save()
  command=['podman','run','--rm','--name','ming-review-'+cell['id'].lower(),'--security-opt','label=disable','--network=none','--device','nvidia.com/gpu='+cell['gpu_uuid'],'--shm-size','32g','-e','CUDA_VISIBLE_DEVICES=0','-e','NVIDIA_VISIBLE_DEVICES='+cell['gpu_uuid'],'-e','PYTHONDONTWRITEBYTECODE=1','-e','HF_HOME=/opt/rsi-assets/huggingface','-e','HF_HUB_OFFLINE=1','-e','HF_DATASETS_OFFLINE=1','-e','TRANSFORMERS_OFFLINE=1','-e','MING_PR_GRAPH_EVENTS=/results/graphs.jsonl','-e','MING_REVIEW_REPLAYS=/results/replays.jsonl','-e','PYTHONPATH=/observe:/workspace/sglang-omni','-v',str(root/cell['arm'])+':/workspace/sglang-omni:ro','-v',str(root/'assets')+':/opt/rsi-assets:rw','-v',str(output)+':/results:rw','-v',str(root/'observe')+':/observe:ro','-v',str(root/'current_run_arm.py')+':/run_arm.py:ro','-w','/workspace/sglang-omni','--entrypoint','/opt/sglang/bin/python3','localhost/ming-review-runtime:20261028','/run_arm.py']
  (output/'container-command.json').write_text(json.dumps(command,indent=2))
  with (output/'execution.log').open('w') as log:p=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
  if p.returncode:raise RuntimeError(f'{cell["id"]} exited{p.returncode}; inspect execution/benchmark/server logs before retry')
  result=json.loads((output/'result.json').read_text());assert result['coverage']=={'en':1088,'zh':2020}[cell['language']];assert result['speed']['failed_requests']==0
  state['completed'].append(cell['id']);save()
 state.update(stage='complete',finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());save()
except Exception as error:
 state.update(stage='failed',error=str(error));save();raise
