"""External graph coverage observer; does not change graph inputs or outputs."""
import atexit,inspect,json,os,time
from pathlib import Path
capture_path=os.environ.get('MING_PR_GRAPH_EVENTS')
replay_path=os.environ.get('MING_REVIEW_REPLAYS')
if capture_path:
 import torch
 validation_seed=os.environ.get('MING_REVIEW_STARTUP_SEED')
 if validation_seed is not None:
  import random,numpy as np
  random.seed(int(validation_seed));np.random.seed(int(validation_seed));torch.manual_seed(int(validation_seed))
 counts={};kinds={}
 original_end=torch.cuda.CUDAGraph.capture_end
 original_replay=torch.cuda.CUDAGraph.replay
 def write(path,event):
  if path:
   event.update(epoch=time.time(),pid=os.getpid())
   with open(path,'a') as stream:stream.write(json.dumps(event)+'\n')
 def capture_end(graph,*args,**kwargs):
  result=original_end(graph,*args,**kwargs)
  names=' '.join(frame.filename for frame in inspect.stack())
  kind='ming_tts_tail' if '/models/ming_tts/sglang_model.py' in names else 'streaming_vae' if '/ming_audio/audio_decode.py' in names else 'sglang_ar' if 'cuda_graph_runner' in names else 'other'
  kinds[id(graph)]=kind;counts[id(graph)]=0
  write(capture_path,{'event':'capture','graph':id(graph),'kind':kind,'cpu_initial_seed':torch.initial_seed(),'cuda_initial_seed':torch.cuda.initial_seed()})
  return result
 def replay(graph,*args,**kwargs):
  result=original_replay(graph,*args,**kwargs);identity=id(graph);count=counts.get(identity,0)+1;counts[identity]=count
  if count==1 or count%8==0:write(replay_path,{'event':'replay','graph':identity,'kind':kinds.get(identity,'unknown'),'count':count})
  return result
 def final():
  for identity,count in counts.items():write(replay_path,{'event':'final_count','graph':identity,'kind':kinds.get(identity,'unknown'),'count':count})
 torch.cuda.CUDAGraph.capture_end=capture_end
 torch.cuda.CUDAGraph.replay=replay
 torch.cuda.CUDAGraph._ming_review_observed=True
 atexit.register(final)
