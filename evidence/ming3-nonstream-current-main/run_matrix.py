"""Run current-main PR3136 qualification and review ablations on the assigned H200."""
from pathlib import Path
import datetime,hashlib,json,subprocess,time
root=Path('/data/zhuofeng-li/home/ming3-current-main-20261027')
uuid='GPU-4ac09667-48f7-6a03-b930-8338f78d441e'
image='localhost/ming3-pr3136:20261026'
state_path=root/'matrix-status.json'
state=json.loads(state_path.read_text()) if state_path.exists() else {'completed':[],'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
def save():
 state['updated_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
 p=root/'matrix-status.partial';p.write_text(json.dumps(state,indent=2));p.replace(state_path)
state['stage']='waiting_release';save()
while not (root/'qualification-release.json').exists():time.sleep(10)
release=json.loads((root/'qualification-release.json').read_text())
assert json.loads((root/'test-status.json').read_text())['stage']=='passed'
assert release['base']=='0fe60cf6c102caf982430e1764243c6e5c749d76'
assert release['candidate_commit'] and release['assignment']=='01M5XFE1DE8PVBQWTSDP2JDYRY'
assert subprocess.check_output(['nvidia-smi','--query-gpu=uuid','--format=csv,noheader'],text=True).strip()==uuid
for name,digest in release['archives'].items():
 assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest
common=['podman','run','--rm','--security-opt','label=disable','--network=none','--device','nvidia.com/gpu='+uuid,'--shm-size','32g','-e','CUDA_VISIBLE_DEVICES=0','-e','NVIDIA_VISIBLE_DEVICES='+uuid,'-e','PYTHONDONTWRITEBYTECODE=1','-e','HF_HUB_OFFLINE=1','-e','HF_DATASETS_OFFLINE=1','-e','TRANSFORMERS_OFFLINE=1','-e','PYTHONPATH=/observe:/workspace/sglang-omni:/opt/rsi-deps/cosyvoice:/opt/rsi-deps/matcha','-w','/workspace/sglang-omni','--entrypoint','/opt/sglang/bin/python3']
plan=[]
# Complete one balanced condition before expanding; all remaining cells retain the same protocol.
cells=[('en',32)]+[(language,concurrency) for language in ['en','zh'] for concurrency in [1,16,32,64] if (language,concurrency)!=('en',32)]
for comparison,control in [('upstream','control'),('lifetime-corrected','corrected-main')]:
 for language,concurrency in cells:
  for label,arm,seed in [('A42',control,42),('B42','candidate',42),('B43','candidate',43),('A43',control,43)]:
   plan.append({'id':f'{comparison}-{language}-c{concurrency}-{label}','comparison':comparison,'language':language,'concurrency':concurrency,'label':label,'arm':arm,'seed':seed,'variant':'native'})
for comparison,variant,cells in [
 ('mps-attribution','mps-off',[(language,c) for language in ['en','zh'] for c in [1,32]]),
 ('cache-attribution','cache-off',[(language,32) for language in ['en','zh']]),
 ('fused-attribution','fused-off',[('en',32)]),
]:
 for language,concurrency in cells:
  for label,mode,seed in [('A42','native',42),('B42',variant,42),('B43',variant,43),('A43','native',43)]:
   plan.append({'id':f'{comparison}-{language}-c{concurrency}-{label}','comparison':comparison,'language':language,'concurrency':concurrency,'label':label,'arm':'candidate','seed':seed,'variant':mode})
(root/'plan.json').write_text(json.dumps(plan,indent=2));state['expected_arms']=len(plan);save()
try:
 for cell in plan:
  identity=cell['id'];output=root/'results'/identity
  current_release=json.loads((root/'qualification-release.json').read_text())
  if time.time()>current_release['lease_expires_epoch']-1800:raise RuntimeError('Lease needs renewal before another arm; completed results retained')
  if identity in state['completed']:
   assert (output/'result.json').is_file();continue
  # A caller must diagnose failures before removing or superseding an existing failed cell.
  output.mkdir(parents=True,exist_ok=False)
  config={**cell,'gpu_uuid':uuid,'candidate_commit':release['candidate_commit'],'base_commit':release['base']}
  (output/'config.json').write_text(json.dumps(config,indent=2))
  state.update(stage='running',active=identity);save()
  command=common+['--name','pr3136-'+identity.lower(),'-v',str(root/cell['arm'])+':/workspace/sglang-omni:ro','-v',str(output)+':/results:rw','-v',str(root/'observe')+':/observe:ro','-v',str(root/'run_arm.py')+':/run_arm.py:ro',image,'/run_arm.py']
  (output/'container-command.json').write_text(json.dumps(command))
  with (output/'execution.log').open('w') as log:outcome=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
  if outcome.returncode:raise RuntimeError(f'{identity}: exit {outcome.returncode}')
  result=json.loads((output/'result.json').read_text());assert result['coverage']=={'en':1088,'zh':2020}[cell['language']]
  assert result['speed']['failed_requests']==0 and result['costs']['peak_tts_device_gib']>0
  state['completed'].append(identity);save()
 state.update(stage='complete',finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat());save()
except Exception as error:
 state.update(stage='failed',error=f'{type(error).__name__}: {error}');save();raise
