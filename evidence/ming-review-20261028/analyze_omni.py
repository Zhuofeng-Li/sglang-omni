from pathlib import Path
import csv,datetime,io,json,statistics,tarfile
r=Path(__file__).resolve().parent
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'expected_arms':32,'arms':[],'paired_cells':[],'scope':'Bounded shared Ming-Omni-TTS regression; first32 SeedTTS per language. Startup/engine RNG42/43, requestseedNone, max_new_tokens256. No independent Tiny performance qualification.'}
with tarfile.open(r/'parallel-omni/latest-backup.tar.gz') as t:
 names=set(t.getnames())
 def load(p):return json.load(t.extractfile(p))
 def rows(p):return {x['id']:x for x in csv.DictReader(io.StringIO(t.extractfile(p).read().decode()))}
 for n in sorted(names):
  if n.startswith('omni-results/') and n.endswith('/result.json'):
   result=load(n);prefix=n.removesuffix('/result.json');events=result['costs']['events'];start=events[0]['epoch'];stop=next(e['epoch'] for e in events if e['event']=='Stopping server' and e['epoch']>start)
   captures=[json.loads(line) for line in t.extractfile(prefix+'/graphs.jsonl').read().decode().splitlines()]
   serving=[e for e in captures if start<=e['epoch']<=stop];assert serving
   assert all(e['cpu_initial_seed']==result['config']['seed'] and e['cuda_initial_seed']==result['config']['seed'] for e in serving),(prefix,serving)
   result['startup_rng_capture_verified']=True;out['arms'].append(result)
 for lang in ['en','zh']:
  for c in [1,8]:
   for stream in [False,True]:
    prefix=f'omni-results/omni-{lang}-c{c}-'+('stream' if stream else 'full')+'-'
    if not all(prefix+label+'/result.json' in names for label in ['A42','B42','B43','A43']):continue
    results={label:load(prefix+label+'/result.json') for label in ['A42','B42','B43','A43']}
    armavg={}
    for arm in ['A','B']:
     x=[results[arm+str(seed)] for seed in [42,43]]
     armavg[arm]={'wer_percent':100*statistics.mean(q['wer']['wer_corpus'] for q in x),'sim':statistics.mean(q['speaker_sim']['mean'] for q in x),'qps':statistics.mean(q['speed']['throughput_qps'] for q in x),'latency_mean_s':statistics.mean(q['speed']['latency_mean_s'] for q in x),'latency_p95_s':statistics.mean(q['speed']['latency_p95_s'] for q in x),'startup_s':statistics.mean(q['costs']['startup_to_ready_s'] for q in x),'peak_device_gib':statistics.mean(q['costs']['peak_tts_device_gib'] for q in x),'captures':statistics.mean(q['costs']['successful_tts_captures'] for q in x),'failed':sum(q['speed']['failed_requests'] for q in x),'attempted':sum(q['speed']['total_requests'] for q in x)}
    pairs=[]
    for seed in [42,43]:
     ap,bp=prefix+'A'+str(seed),prefix+'B'+str(seed);a,b=rows(ap+'/output/wer_results.csv'),rows(bp+'/output/wer_results.csv');ah,bh=load(ap+'/audio_sha256.json'),load(bp+'/audio_sha256.json');assert a.keys()==b.keys()
     assert all(a[k]['target_text']==b[k]['target_text'] for k in a)
     ae,be,den=0,0,0;changes=[]
     for k in a:
      ac=sum(int(a[k][v]) for v in ['substitutions','deletions','insertions']);bc=sum(int(b[k][v]) for v in ['substitutions','deletions','insertions']);ae+=ac;be+=bc;den+=sum(int(a[k][v]) for v in ['hits','substitutions','deletions'])
      if a[k]['whisper_text']!=b[k]['whisper_text']:changes.append({'id':k,'target':a[k]['target_text'],'control':a[k]['whisper_text'],'candidate':b[k]['whisper_text'],'control_edits':ac,'candidate_edits':bc,'same_wav':ah[k]==bh[k]})
     pairs.append({'seed':seed,'control_edits':ae,'candidate_edits':be,'reference_units':den,'same_wav':sum(ah[k]==bh[k] for k in a),'transcript_changes':changes})
    out['paired_cells'].append({'language':lang,'concurrency':c,'stream':stream,'mean':armavg,'pairs':pairs})
out['completed_arms']=len(out['arms']);(r/'omni-analysis.json').write_text(json.dumps(out,indent=2,ensure_ascii=False))
print('Completed arms',out['completed_arms'],'paired cells',len(out['paired_cells']))
for x in out['paired_cells']:print(json.dumps({k:v for k,v in x.items() if k!='pairs'},ensure_ascii=False))
