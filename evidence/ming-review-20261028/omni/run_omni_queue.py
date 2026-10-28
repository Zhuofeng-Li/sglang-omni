from pathlib import Path
import datetime,json,subprocess,time
r=Path(__file__).resolve().parent
state_path=r/'omni-queue-status.json'
if state_path.exists():raise RuntimeError('Existing state; diagnose/resume explicitly')
while True:
 p=r/'bootstrap-status.json'
 if p.exists():
  status=json.loads(p.read_text())
  if status['stage']=='failed':raise RuntimeError(status)
  if status['stage']=='ready':break
 time.sleep(15)
assert len(json.loads((r/'source-receipts.json').read_text()))==2
plan=[]
for language in ['en','zh']:
 for concurrency in [1,8]:
  for stream in [False,True]:
   for label,arm,seed in [('A42','omni-control',42),('B42','omni-candidate',42),('B43','omni-candidate',43),('A43','omni-control',43)]:
    plan.append({'id':f'omni-{language}-c{concurrency}-'+('stream' if stream else 'full')+'-'+label,'language':language,'concurrency':concurrency,'stream':stream,'label':label,'arm':arm,'seed':seed,'variant':'native','gpu_uuid':'GPU-da0d9c21-eb80-f5c6-c12c-bfc5bcb9f207','model_revision':'2efcd28d04f83b1bd471af639b4210c9ecf2cd33','control_source':'d57f2e970df64266b04e09bf716ba0ecc2342eca','candidate_source':'96957d08e9dcd260005f5e92b9d13e90c544bbcf'})
(r/'omni-plan.json').write_text(json.dumps(plan,indent=2));state={'stage':'starting','expected':len(plan),'completed':[],'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
def save():
 state['utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();p=r/'omni-state.partial';p.write_text(json.dumps(state,indent=2));p.replace(state_path)
save()
try:
 for cell in plan:
  if time.time()>1793237369-1800:raise RuntimeError('Lease needs verified extension before another arm')
  output=r/'omni-results'/cell['id'];output.mkdir(parents=True,exist_ok=False);(output/'config.json').write_text(json.dumps(cell,indent=2));state.update(stage='running',active=cell['id']);save()
  command=['podman','run','--rm','--name','ming-review-'+cell['id'].lower(),'--security-opt','label=disable','--network=none','--device','nvidia.com/gpu='+cell['gpu_uuid'],'--shm-size','32g','-e','MING_REVIEW_STARTUP_SEED='+str(cell['seed']),'-e','CUDA_VISIBLE_DEVICES=0','-e','NVIDIA_VISIBLE_DEVICES='+cell['gpu_uuid'],'-e','PYTHONDONTWRITEBYTECODE=1','-e','HF_HOME=/opt/rsi-assets/huggingface','-e','HF_HUB_OFFLINE=1','-e','HF_DATASETS_OFFLINE=1','-e','TRANSFORMERS_OFFLINE=1','-e','MING_PR_GRAPH_EVENTS=/results/graphs.jsonl','-e','MING_REVIEW_REPLAYS=/results/replays.jsonl','-e','PYTHONPATH=/observe:/workspace/sglang-omni','-v',str(r/cell['arm'])+':/workspace/sglang-omni:ro','-v',str(r/'assets')+':/opt/rsi-assets:rw','-v',str(output)+':/results:rw','-v',str(r/'omni-observe')+':/observe:ro','-v',str(r/'run_ming_omni_arm.py')+':/run_arm.py:ro','-w','/workspace/sglang-omni','--entrypoint','/opt/sglang/bin/python3','localhost/ming-review-runtime:20261028','/run_arm.py']
  (output/'container-command.json').write_text(json.dumps(command,indent=2))
  with (output/'execution.log').open('w') as log:p=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
  if p.returncode:raise RuntimeError(f'{cell["id"]} exit{p.returncode}; inspect logs, do not silently retry')
  result=json.loads((output/'result.json').read_text());assert result['coverage']==32 and result['speed']['failed_requests']==0;assert result['serving_graph_coverage']['ming_tts_tail']['serving_replay_observations']>0
  state['completed'].append(cell['id']);save()
 state.update(stage='complete',finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());save()
except Exception as error:
 state.update(stage='failed',error=str(error));save();raise
