"""Retain bounded startup/cache excerpts omitted by tail-only result backups."""
from pathlib import Path
import json
import subprocess

root = Path(__file__).resolve().parent
remote = '''from pathlib import Path
import json,re,time,subprocess,os
r=Path.home()/'ming-final-review-20261031'
queue=json.loads((r/'queue-status.json').read_text())
rows=[]
for arm in queue['completed']:
 folder=r/'results'/arm
 excerpts=[]
 for path in (folder/'output/server_logs').glob('*.log'):
  for line in path.read_text(errors='replace').splitlines():
   if re.search(r'MPS daemon ready|MPS summary|reference.cache|cache.{0,15}(?:hits|misses|merges)',line,re.I):
    excerpts.append({'log':path.name,'line':line[-1500:]})
 assert len(excerpts)<1000,(arm,'unexpected excerpt volume')
 rows.append({'arm':arm,'config':json.loads((folder/'config.json').read_text()),'excerpts':excerpts})
processes=subprocess.run(['ps','-u',str(os.getuid()),'-o','pid,args'],capture_output=True,text=True,check=True).stdout.splitlines()
print(json.dumps({'epoch':time.time(),'completed_arms':rows,
 'active_arm':queue.get('active'),'queue_stage':queue['stage'],
 'mps_processes_for_assignment_user':[line for line in processes if 'nvidia-cuda-mps' in line],
 'scope':'Informational startup/cache excerpts only; no measurement process or source was changed.'}))
'''
result = subprocess.run(['python', str(root / 'node.py'), '--python'], input=remote,
                        text=True, capture_output=True, check=True, timeout=60)
data = json.loads(result.stdout)
(root / 'runtime-log-excerpts.json').write_text(json.dumps(data, indent=2) + '\n')
print(json.dumps({'arms': len(data['completed_arms']),
                  'excerpts': {a['arm']: len(a['excerpts']) for a in data['completed_arms']}}))
