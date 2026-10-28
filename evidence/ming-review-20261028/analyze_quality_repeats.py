from pathlib import Path
import csv,datetime,io,json,tarfile
r=Path(__file__).resolve().parent

class MetricArchive:
 def __init__(self,path):
  self.data={}
  with tarfile.open(path,mode='r|gz') as source:
   for member in source:
    if member.isfile() and member.name.startswith(('quality-results/','results/lifetime-corrected-')) and Path(member.name).name in ['wer_results.csv','audio_sha256.json','result.json']:
     self.data[member.name]=source.extractfile(member).read()
 def extractfile(self,name):return io.BytesIO(self.data[name])
 def getnames(self):return list(self.data)
 def __enter__(self):return self
 def __exit__(self,*args):pass

def load(t,p):return json.load(t.extractfile(p))
def rows(t,p):return {q['id']:q for q in csv.DictReader(io.StringIO(t.extractfile(p).read().decode()))}
def compare(t1,p1,t2,p2):
 a,b=rows(t1,p1+'/output/wer_results.csv'),rows(t2,p2+'/output/wer_results.csv');assert a.keys()==b.keys()
 ah,bh=load(t1,p1+'/audio_sha256.json'),load(t2,p2+'/audio_sha256.json')
 totals={'samples':len(a),'reference_units':0,'left_errors':0,'right_errors':0,'same_waveform':0,'same_waveform_changed_transcript':0,'changed_transcript':0,'worse':0,'better':0}
 differences=[]
 for k,x in a.items():
  y=b[k];assert x['target_text']==y['target_text'];ec=[sum(int(z[v]) for v in ['substitutions','deletions','insertions']) for z in [x,y]];den=sum(int(x[v]) for v in ['hits','substitutions','deletions']);totals['reference_units']+=den
  totals['left_errors']+=ec[0];totals['right_errors']+=ec[1];same=ah[k]==bh[k];changed=x['whisper_text']!=y['whisper_text'];totals['same_waveform']+=same;totals['changed_transcript']+=changed;totals['same_waveform_changed_transcript']+=same and changed;totals['worse']+=ec[1]>ec[0];totals['better']+=ec[1]<ec[0]
  if changed:differences.append({'id':k,'target':x['target_text'],'left_transcript':x['whisper_text'],'right_transcript':y['whisper_text'],'left_errors':ec[0],'right_errors':ec[1],'same_waveform':same})
 totals['delta_pp']=100*(totals['right_errors']-totals['left_errors'])/totals['reference_units'];return {'totals':totals,'differences':differences}
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'comparisons':[],'note':'Same historical source/checkpoint/data/scorer identities, new node runtime. Legacy whisper_text CSV column is Qwen3-ASR. Hash identity is exact WAV file identity. No listening claim or formal non-inferiority threshold.'}
with MetricArchive(r/'latest-backup.tar.gz') as new,MetricArchive(r.parent/'current-results-backup.tar.gz') as old:
 names=set(new.getnames())
 for language,c in [('en',16),('zh',1)]:
  def p(label):return f'quality-results/quality-{language}-c{c}-{label}'
  pairs=[('A42','B42'),('A43','B43'),('A42','repeat-A42'),('A43','repeat-A43')]
  for x,y in pairs:
   if all(p(z)+'/result.json' in names for z in [x,y]):report['comparisons'].append({'language':language,'left':x,'right':y,'scope':'fresh-vs-fresh',**compare(new,p(x),new,p(y))})
  for label in ['A42','B42','B43','A43']:
   if p(label)+'/result.json' in names:report['comparisons'].append({'language':language,'left':'historical-'+label,'right':'fresh-'+label,'scope':'historical-vs-fresh',**compare(old,f'results/lifetime-corrected-{language}-c{c}-{label}',new,p(label))})
(r/'quality-repeat-analysis.json').write_text(json.dumps(report,indent=2,ensure_ascii=False))
for q in report['comparisons']:print(json.dumps({k:v for k,v in q.items() if k!='differences'}))
