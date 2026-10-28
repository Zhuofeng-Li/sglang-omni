"""Publish only complete quality-repeat evidence; original benchmark stays unchanged."""
from pathlib import Path
import csv,hashlib,io,json,shutil,tarfile
r=Path(__file__).resolve().parent;e=r.parent/'evidence-repo/evidence/ming-review-20261028'
analysis=json.loads((r/'quality-repeat-analysis.json').read_text())
assert sum(x['totals']['same_waveform'] for x in analysis['comparisons'] if x['scope']=='historical-vs-fresh' and x['language']=='zh')==8080
selected={
 ('en',42,'common_voice_en_25568854-common_voice_en_25568851'),
 ('en',42,'common_voice_en_18057869-common_voice_en_18057867'),
 ('en',43,'common_voice_en_19211875-common_voice_en_19211870'),
 ('zh',42,'00004504-00000057'),('zh',42,'00013652-00000048'),
 ('zh',43,'00005257-00000065'),('zh',43,'00004895-00000090'),
}
allowed={'result.json','config.json','command.json','server-config.yaml','resolved-pipeline.json','runtime.json','graphs.jsonl','replays.jsonl','audio_sha256.json','speaker_similarity.json','container-command.json','output/wer_results.csv','output/wer_results.json','output/generated.json'}
root_files={'source-receipts.json','runtime-freeze.txt','runtime-image.json','current_run_arm.py','run_quality_queue.py','quality-plan.json','quality-queue-status.json','observe/sitecustomize.py'}
desired_wavs={f"quality-results/quality-{lang}-c{16 if lang=='en' else 1}-{arm}{seed}/output/audio/{sample}.wav" for lang,seed,sample in selected for arm in ['A','B']}
class EvidenceArchive:
 def __init__(self,path):
  self.data={};self.members=[]
  with tarfile.open(path,mode='r|gz') as source:
   for member in source:
    if not member.isfile():continue
    p=Path(member.name);include=member.name in root_files or member.name in desired_wavs
    if len(p.parts)>2 and p.parts[0]=='quality-results':include=include or Path(*p.parts[2:]).as_posix() in allowed
    if member.name.startswith('results/lifetime-corrected-') and p.name=='audio_sha256.json':include=True
    if include:self.members.append(member);self.data[member.name]=source.extractfile(member).read()
 def extractfile(self,member):return io.BytesIO(self.data[member if isinstance(member,str) else member.name])
 def getmembers(self):return self.members
 def __enter__(self):return self
 def __exit__(self,*args):pass
index=[];results={}
with EvidenceArchive(r/'latest-backup.tar.gz') as t,EvidenceArchive(r.parent/'current-results-backup.tar.gz') as old:
 state=json.load(t.extractfile('quality-queue-status.json'));assert state['stage']=='complete' and len(state['completed'])==12
 for label in state['completed']:results[label]=json.load(t.extractfile(f'quality-results/{label}/result.json'))
 assert sum(x['speed']['completed_requests'] for x in results.values())==18648
 assert all(x['speed']['failed_requests']==0 for x in results.values())
 chosen=set()
 for language,seed,sample in selected:
  c=16 if language=='en' else 1
  for arm in ['A','B']:
   label=f'quality-{language}-c{c}-{arm}{seed}';chosen.add((label,sample))
 for member in t.getmembers():
  if not member.isfile():continue
  p=Path(member.name);assert not p.is_absolute() and '..' not in p.parts
  include=member.name in root_files
  if len(p.parts)>2 and p.parts[0]=='quality-results':
   include=Path(*p.parts[2:]).as_posix() in allowed
   if len(p.parts)==5 and p.parts[2:4]==('output','audio'):
    include=(p.parts[1],p.stem) in chosen
    if include:
     label=p.parts[1];expected=json.load(t.extractfile(f'quality-results/{label}/audio_sha256.json'))[p.stem];payload=t.extractfile(member).read();assert hashlib.sha256(payload).hexdigest()==expected
     hist_label=label.removeprefix('quality-');historical=json.load(old.extractfile(f'results/lifetime-corrected-{hist_label}/audio_sha256.json'))[p.stem]
     index.append({'arm':label,'sample_id':p.stem,'sha256':expected,'historical_sha256':historical,'historical_waveform_reproduced_exactly':expected==historical,'file':'quality/'+member.name})
  if include:
   target=e/'quality'/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(t.extractfile(member).read())
assert len(index)==14
(e/'quality-audio-index.json').write_text(json.dumps(index,indent=2));(e/'quality-results.json').write_text(json.dumps(results,indent=2))
for n in ['quality-repeat-analysis.json','paired-error-inspection.json','historical-fresh-runtime-comparison.json','analyze_paired_errors.py','analyze_quality_repeats.py']:
 shutil.copy2(r/n,e/n)
shutil.copy2(r/'backup-status.json',e/'quality-backup-receipt.json')
by_key={(x['language'],x['left'],x['right']):x for x in analysis['comparisons']}
lines=['## #3136 requested quality follow-up','',
 '**Complete:** 12 arms / 18,648 formal requests, zero failures. Full EN 1,088 and ZH 2,020 per arm. Per cell the order is A42,B42,B43,A43,repeat-A42,repeat-A43 on one H200 `GPU-99e2ecd1-862a-4af1-222d-841708198f30`. Historical corrected-control source `0d6a414e5e15c996900620d263143c89e0dd8acd` and candidate `3f8593f4cae19fe1c71e929a854bdc03b2c185e6` were frozen throughout. These are review-requested source reproductions, not speedup measurements on today’s main. A read-only Hugging Face cache preflight failed before formal requests; the assets mount was made writable for normal snapshot bookkeeping, with the same mount/runtime policy in every accepted arm. Its failure evidence was retained separately.',
 '', 'Model `inclusionAI/Ming-3.0-tts-0.5B@8d66b70a00f05ad183fa8a863b4ce609fc83cbc0`; data `zhaochenyang20/seed-tts-eval-arrow@27f4c1adee83b5b29b7c4b375f6b976324bda308`; scorer `Qwen/Qwen3-ASR-1.7B@7278e1e70fe206f11671096ffdd38061171dd6e5`; fixed CAM++. Original operator/evaluator and full-split request order retained, per-request seed42/43, nonstream, max-running/graph64, fresh service/cache per arm, native default CPU scheduling. All fresh arms share the same runtime. [Recorded historical/fresh runtime comparison](historical-fresh-runtime-comparison.json) discloses the Torch distribution strings2.14.1 versus2.14.1+cu130; no binary-identical runtime claim. The legacy CSV column `whisper_text` contains Qwen ASR output.',
 '', '| Split/c | Seed | Historical A/B edits | Fresh A/B edits | Fresh Δ WER (pp) | Repeated A edits | Repeat Δ WER (pp) | Fresh SIM A → B |', '|---|---:|---:|---:|---:|---:|---:|---:|']
for lang,c in [('en',16),('zh',1)]:
 for seed in [42,43]:
  z=by_key[(lang,'A'+str(seed),'B'+str(seed))]['totals'];rep=by_key[(lang,'A'+str(seed),'repeat-A'+str(seed))]['totals'];hist=next(x for x in json.loads((r/'paired-error-inspection.json').read_text())['cells'] if x['language']==lang and x['seed']==seed)['totals'];aa=results[f'quality-{lang}-c{c}-A{seed}'];bb=results[f'quality-{lang}-c{c}-B{seed}']
  lines.append(f"| {lang.upper()} c{c} | {seed} | {hist['control_errors']}/{hist['candidate_errors']} | {z['left_errors']}/{z['right_errors']} | {z['delta_pp']:+.6f} | {rep['right_errors']} | {rep['delta_pp']:+.6f} | {aa['speaker_sim']['mean']:.6f} → {bb['speaker_sim']['mean']:.6f} |")
lines += ['', 'Denominators are 11,943 EN reference units and 42,266 ZH reference units. Original corrected-control positive WER deltas are preserved, not overwritten. Fresh EN signs differ between seeds; fresh ZH positive deltas remain visible. Repeated controls and exactly identical WAVs with different transcriptions demonstrate scorer variability, not non-inferiority or a proof that every quality difference is evaluator noise.', '', '| Comparison | Same WAVs | Same-WAV changed ASR transcripts | Net edit change |', '|---|---:|---:|---:|']
for x in analysis['comparisons']:
 if (x['scope']=='fresh-vs-fresh' and x['right'].startswith('repeat-')) or (x['language']=='zh' and x['scope']=='historical-vs-fresh'):
  z=x['totals'];lines.append(f"| {x['language'].upper()} {x['left']} → {x['right']} | {z['same_waveform']}/{z['samples']} | {z['same_waveform_changed_transcript']} | {z['right_errors']-z['left_errors']:+d} |")
lines += ['', '[Original affected transcript inspection](paired-error-inspection.json) includes segmentation (moon bounce/moonbounce), number rendering (二零零九/2009), homophones and lexical changes. [Fresh paired and same-control transcript differences](quality-repeat-analysis.json) retain all examples. [Selected affected recordings with hashes](quality-audio-index.json) explicitly identify exact historical waveform reconstructions; fresh EN recordings are not mislabeled as old files. No claim of listening to original unavailable recordings is made.', '', 'The reviewer is asked to assess these measured quality differences; no formal equivalence margin was specified or inferred. Current CI/correctness checks are separately reported above. Original 92-arm throughput/ablation qualification retains its actual dates/revisions and remains linked in Prior complete records.', '']
p=e/'report.md';s=p.read_text();start=s.index('## #3136 requested quality follow-up');end=s.index('## #3217 requested shared-model validation',start);s=s[:start]+'\n'.join(lines)+'\n'+s[end:];s=s.replace('Status: current-head code/CI checks complete; requested quality validation is running. This report does not qualify #3217 for release.','Status: current-head code/CI and the requested quality follow-up are complete; quality acceptance and required reviews remain pending. This report does not qualify #3217 for release.');s=s.replace('#3136 quality-repeat completion and reviewer approval;','#3136 quality assessment and reviewer approval;');p.write_text(s)
print('Exported all12 quality arms, paired inspection and14 selected affected waveforms; original PR/body/review publication still required')
