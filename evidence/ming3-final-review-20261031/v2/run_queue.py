from pathlib import Path
import datetime,json,subprocess,time
r=Path(__file__).resolve().parent
plan=json.loads((r/'measurement-plan.json').read_text())
status_path=r/'queue-status.json'
if status_path.exists():raise RuntimeError('Existing queue must be inspected before resume')
state={'stage':'waiting_regression','completed':[],'expected':len(plan),'started_epoch':time.time()}
def save():
 state['epoch']=time.time();p=r/'queue-status.partial';p.write_text(json.dumps(state,indent=2));p.replace(status_path)
save()
try:
 while not (r/'gpu-tests-v2-result.json').exists():time.sleep(5)
 assert json.loads((r/'gpu-tests-v2-result.json').read_text())['exit_code']==0
 assert 'benchmark_import_ok' in (r/'warm-dataset.log').read_text()
 assert (r/'assets-ready').exists()
 image='localhost/ming-final-review:20261031-v2'
 state['image']=json.loads(subprocess.check_output(['docker','inspect',image]))[0]['Id'];save()
 for cell in plan:
  if time.time()>1793494161-1800:raise RuntimeError('Allocation end approaching; preserve and inspect lease')
  output=r/'results'/cell['id'];output.mkdir(parents=True,exist_ok=False);(output/'config.json').write_text(json.dumps(cell,indent=2));state.update(stage='running',active=cell['id']);save()
  command=['docker','run','--rm','--name','ming-final-'+cell['id'].lower(),'--security-opt','label=disable','--network=none','--device','nvidia.com/gpu='+cell['gpu_uuid'],'--shm-size','32g','-e','CUDA_VISIBLE_DEVICES=0','-e','NVIDIA_VISIBLE_DEVICES='+cell['gpu_uuid'],'-e','PYTHONDONTWRITEBYTECODE=1','-e','HF_HOME=/opt/rsi-assets/huggingface','-e','HF_HUB_OFFLINE=1','-e','HF_DATASETS_OFFLINE=1','-e','TRANSFORMERS_OFFLINE=1','-e','MING_PR_GRAPH_EVENTS=/results/graphs.jsonl','-e','PYTHONPATH=/observe:/workspace/sglang-omni','-v',str(r/cell['arm'])+':/workspace/sglang-omni:ro','-v',str(r/'assets')+':/opt/rsi-assets:rw','-v',str(output)+':/results:rw','-v',str(r/'observe')+':/observe:ro','-v',str(r/'run_arm.py')+':/run_arm.py:ro','-w','/workspace/sglang-omni','--entrypoint','/opt/sglang/bin/python3',image,'/run_arm.py']
  (output/'container-command.json').write_text(json.dumps(command,indent=2))
  with (output/'execution.log').open('w') as log:p=subprocess.run(command,stdout=log,stderr=subprocess.STDOUT)
  if p.returncode:raise RuntimeError(cell['id']+' failed; inspect saved logs before retry')
  result=json.loads((output/'result.json').read_text());assert result['coverage']=={'en':1088,'zh':2020}[cell['language']];assert result['speed']['failed_requests']==0
  state['completed'].append(cell['id']);save()
 state.update(stage='complete',finished_epoch=time.time());save()
except BaseException as error:
 state.update(stage='failed',error=type(error).__name__+': '+str(error));save();raise
