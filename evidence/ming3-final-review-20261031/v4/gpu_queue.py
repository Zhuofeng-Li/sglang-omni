from pathlib import Path
import subprocess,json,time,hashlib
r=Path.home()/'ming-review-20261101-defaults'
im='docker.io/hongccc/sglang-omni@sha256:06ed306707bcf3d9e9beb5ba7ce66f09a666cac11c23455ece50c34199c0e985'
uuid='GPU-da0d9c21-eb80-f5c6-c12c-bfc5bcb9f207'
state={'started_epoch':time.time(),'completed':[]}
def save(): (r/'queue-status.json').write_text(json.dumps(state,indent=2))
def run(name,src,args,extra=(),expected=0):
 out=r/name;out.mkdir(exist_ok=False)
 cmd=['docker','run','--rm','--name','review-'+name,'--security-opt','label=disable','--shm-size','16g','--device','nvidia.com/gpu='+uuid,'-e','SGLANG_OMNI_AUTO_CLONE=0','-e','PYTHONDONTWRITEBYTECODE=1','-e','PYTHONPATH=/workspace/sglang-omni:/workspace/sglang-omni/python','-v',str(r/src)+':/workspace/sglang-omni:ro','-v',str(out)+':/results:rw','-w','/workspace/sglang-omni','--entrypoint','/opt/sglang/bin/python3',*extra,im,*args]
 state.update(stage=name,command=cmd);save()
 with (out/'run.log').open('w') as log:p=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
 state['completed'].append({'name':name,'exit':p.returncode,'expected':expected});save()
 if p.returncode!=expected:raise RuntimeError(f'{name}: exit {p.returncode}, expected {expected}')
try:
 cfg=r/'pr3190/sglang_omni/models/ming3_tts/config.py'
 before=cfg.read_text().replace('                enable_dense_streaming=dense,\n','')
 assert before!=cfg.read_text();(r/'config-before.py').write_text(before)
 mount=['-v',str(r/'config-before.py')+':/workspace/sglang-omni/sglang_omni/models/ming3_tts/config.py:ro']
 run('3190-red','pr3190',['-m','pytest','-q','-p','no:cacheprovider','tests/unit_test/ming3_tts/test_streaming_vocoder.py','-k','gpu_generation_retains_full_latents_for_cpu_vocoder','--junitxml=/results/junit.xml'],mount,1)
 run('3190-green','pr3190',['-m','pytest','-q','-p','no:cacheprovider','tests/unit_test/ming3_tts/test_streaming_vocoder.py','tests/unit_test/ming3_tts/test_ming3_tts_pipeline.py','tests/unit_test/ming_tts/test_streaming_vocoder.py','--junitxml=/results/junit.xml'])
 run('47129-allocator','pr47129',['test/registered/kernels/ops/memory/test_paged_allocator.py','-v'])
 assets=r/'assets';(assets/'seed-data').symlink_to(assets/'seed-data-parent/data',target_is_directory=True)
 out=r/'http-default';out.mkdir()
 model='/hf-cache/models--inclusionAI--Ming-3.0-tts-0.5B/snapshots/8d66b70a00f05ad183fa8a863b4ce609fc83cbc0'
 extras=['-v',str(r/'hf-cache')+':/hf-cache:ro','-v',str(assets)+':/assets:ro','-v',str(r/'validate_integration.py')+':/validate_http.py:ro','-v',str(out)+':/validation:rw','-e','MING_VALIDATION_MODEL='+model]
 run('3190-default-http','pr3190',['/validate_http.py'],extras)
 state['stage']='complete';save()
except BaseException as e:
 state.update(stage='failed',error=repr(e));save();raise
