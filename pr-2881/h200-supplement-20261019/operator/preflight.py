import hashlib, importlib.metadata as m, json, os, subprocess, time
from pathlib import Path
import torch
R=Path(os.environ['QUAL_ROOT'])
assert torch.cuda.device_count()==1
uuid=subprocess.check_output(['nvidia-smi','--query-gpu=uuid','--format=csv,noheader'],text=True).strip()
assert uuid=='GPU-2396c1ff-41ff-385f-30fe-0272d99c5d6c',uuid
packages={name:m.version(name) for name in ['torch','sglang','transformers','flashinfer-python','triton','huggingface-hub','datasets','numpy','jiwer']}
expected=json.loads((R/'control/software-identity.json').read_text())['packages']
for name,version in expected.items():
 assert m.version(name)==version,(name,m.version(name),version)
from benchmarks.dataset.seedtts import load_seedtts_samples
from benchmarks.eval.benchmark_asr_seedtts import run_asr_seedtts_once
assert m.version('RapidFuzz')=='3.14.6'
samples={}
for lang,count in [('en',1088),('zh',2020)]:
 s=load_seedtts_samples('zhaochenyang20/seed-tts-eval-arrow',split=lang,revision='27f4c1adee83b5b29b7c4b375f6b976324bda308')
 assert len(s)==count
 samples[lang]={'count':len(s),'ids_sha256':hashlib.sha256('\n'.join(x.sample_id for x in s).encode()).hexdigest()}
record={'at':time.time(),'gpu_uuid':uuid,'gpu_name':torch.cuda.get_device_name(0),'packages':packages,'samples':samples,'cpu_affinity':sorted(os.sched_getaffinity(0)),'cpu_policy':'default shared, same for every arm','source_sha256':{str(p.relative_to(R)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [R/'source/main/sglang_omni/scheduling/omni_scheduler.py',R/'source/pr-2881/sglang_omni/scheduling/omni_scheduler.py']}}
(R/'control/preflight.json').write_text(json.dumps(record,indent=2))
print(json.dumps(record),flush=True)
