from pathlib import Path
import json,subprocess,sys,os,time
r=Path('/work');parent=Path('/source-stack')
probe='''import json,sys
sys.path.insert(0,sys.argv[1])
from sglang_omni.models.ming3_tts import config as m
out={}
for dense in [False,True]:
 m.try_resolve_ming3_dense_tts=lambda *a,**kw:m.DENSE_ARCHITECTURE if dense else None
 for mode in ['default','off','on','auto']:
  values={'model_path':'test/Ming3-TTS'}
  if mode!='default':values['mps']=mode
  out[str(dense)+'/'+mode]=m.Ming3TTSPipelineConfig(**values).model_dump(mode='json')
print(json.dumps(out,sort_keys=True))
'''
results={}
for key,folder in [('3136','candidate3136'),('3189','candidate3189-final'),('3190','integrated-final')]:
 old=json.loads(subprocess.check_output([sys.executable,'-c',probe,str(parent/'qualification-v2'/folder)],text=True))
 new=json.loads(subprocess.check_output([sys.executable,'-c',probe,str(parent/'qualification-v3'/folder)],text=True))
 for dense in [False,True]:
  for mode in ['default','off','on','auto']:
   k=str(dense)+'/'+mode
   if mode=='default':
    expected=dict(old[k]);expected['mps']='off'
    assert new[k]==expected,(key,k)
   else:assert new[k]==old[k],(key,k)
 results[key]={'default_off_only_change':True,'explicit_off_on_auto_unchanged':True,'config_cases':8}
(r/'config-equivalence.json').write_text(json.dumps({'verified_epoch':time.time(),'results':results,'method':'Real pipeline and schema classes in pinned node runtime; checkpoint architecture mocked as in unit tests. All resolved fields compared, Tiny and dense.'},indent=2))
print('24 config-equivalence cases passed')
