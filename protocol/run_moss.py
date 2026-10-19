"""Backfill requested MOSS c1/c64 under matched two-seed ABBA conditions."""
import json, os, signal, subprocess, sys, time
from pathlib import Path
R=Path('/qualification')
smoke='--smoke' in sys.argv
state=R/'control/moss-state.json'
def save(value):
 value['at']=time.time();p=state.with_suffix('.partial');p.write_text(json.dumps(value,indent=2));p.replace(state)
if not smoke:
 regression=R/'control/moss-regression.exit'
 if not regression.exists() or regression.read_text().strip()!='0':
  regression_env=dict(os.environ,PYTHONPATH=str(R/'source/pr-2859'),OMP_NUM_THREADS='8',MKL_NUM_THREADS='8')
  with (R/'control/moss-regression.log').open('w') as output:
   regression_code=subprocess.run([sys.executable,'-m','pytest','-q','tests/unit_test/moss_tts'],cwd=R/'source/pr-2859',env=regression_env,stdout=output,stderr=subprocess.STDOUT,timeout=1800).returncode
  regression.write_text(str(regression_code))
  if regression_code:raise RuntimeError('Integrated MOSS regression failed; inspect moss-regression.log')
for concurrency in ([1] if smoke else [1,64]):
 for mode in (['nonstream'] if smoke else ['nonstream','stream']):
  for arm,seed in ([('main',42),('pr',42)] if smoke else [('main',42),('pr',42),('pr',43),('main',43)]):
   tag=f'pr2859-c{concurrency}-{mode}-{arm}-seed{seed}'+('-smoke' if smoke else '')
   out=R/'moss-results'/tag;out.mkdir(parents=True,exist_ok=True)
   result_path=out/'result.json'
   if result_path.exists() and json.loads(result_path.read_text()).get('exit_code')==0:continue
   if result_path.exists():
    attempt=int(time.time());result_path.rename(out/f'failed-attempt-{attempt}.json')
    if (out/'operator.log').exists():(out/'operator.log').rename(out/f'failed-attempt-{attempt}.log')
   source=R/'source'/('main' if arm=='main' else 'pr-2859')
   config={'config_cls':'MossTTSPipelineConfig','model_path':str(R/'assets/moss'),'stages':{'preprocessing':{'factory':{'codec_model_path':str(R/'assets/codec')}},'tts_engine':{'gpu_memory_fraction':0.60},'vocoder':{'factory':{'codec_model_path':str(R/'assets/codec')}}}}
   import yaml
   (out/'config.yaml').write_text(yaml.safe_dump(config))
   env=dict(os.environ,PYTHONPATH=str(R/'control/telemetry')+':'+str(source),PYTHONHASHSEED=str(seed),OMP_NUM_THREADS='8',MKL_NUM_THREADS='8',QUAL_GRAPH_DIR=str(out/'graphs'),TOKENIZERS_PARALLELISM='false',SGLANG_ENABLE_JIT_DEEPGEMM='0',SEEDTTS_SIM_CACHE_DIR=str(R/'cache/sim'))
   for name in ['TORCHINDUCTOR_CACHE_DIR','TRITON_CACHE_DIR','CUDA_CACHE_PATH','TORCH_EXTENSIONS_DIR','SGLANG_JIT_CACHE_DIR','FLASHINFER_WORKSPACE_BASE']:
    env[name]=str(R/'moss-compile'/tag/name);Path(env[name]).mkdir(parents=True,exist_ok=True)
   cmd=[sys.executable,str(R/'control/pinned_tts_benchmark.py'),'--generate-only','--port',str(19860+(0 if smoke else 100)+[1,64].index(concurrency)*8+['nonstream','stream'].index(mode)*4+[('main',42),('pr',42),('pr',43),('main',43)].index((arm,seed))),'--model',str(R/'assets/moss'),'--server-config',str(out/'config.yaml'),'--meta','zhaochenyang20/seed-tts-eval-arrow','--ref-format','references','--token-count','auto','--concurrency',str(concurrency),'--warmup','16','--seed',str(seed),'--max-new-tokens','2048','--server-timeout','1200','--skip-gpu-cleanup','--output-dir',str(out)]
   if smoke:cmd+=['--max-samples','4']
   if mode=='stream':cmd+=['--stream']
   gpu_uuid=subprocess.check_output(['nvidia-smi','--query-gpu=uuid','--format=csv,noheader'],text=True).strip()
   assert gpu_uuid=='GPU-e9f60c1d-8856-043c-42cd-47a942a4d8f1'
   start=time.time();peak=0
   with (out/'operator.log').open('w') as log:
    child=subprocess.Popen(cmd,cwd=source,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    while child.poll() is None:
     mem=subprocess.run(['nvidia-smi','--query-gpu=memory.used','--format=csv,noheader,nounits'],capture_output=True,text=True)
     if mem.returncode==0:peak=max(peak,int(mem.stdout.strip()))
     save({'status':'running','cohort':tag,'pid':child.pid,'elapsed':time.time()-start,'peak_mib':peak})
     if time.time()-start>10800:os.killpg(child.pid,signal.SIGTERM);child.wait(timeout=30);break
     time.sleep(.5)
   result={'tag':tag,'arm':arm,'seed':seed,'concurrency':concurrency,'mode':mode,'source':str(source),'gpu_uuid':gpu_uuid,'started_at':start,'finished_at':time.time(),'command':cmd,'exit_code':child.returncode,'elapsed_s':time.time()-start,'peak_mib':peak}
   result_path.write_text(json.dumps(result,indent=2));save(result)
   if child.returncode:raise RuntimeError(f'{tag} exited {child.returncode}')
save({'status':'smoke_complete' if smoke else 'generation_complete'})
