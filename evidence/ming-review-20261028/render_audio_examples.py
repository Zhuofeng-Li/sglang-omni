from pathlib import Path
import csv,collections,json
r=Path(__file__).resolve().parent;e=r.parent/'evidence-repo/evidence/ming-review-20261028';lines=['# Selected paired audio examples','', 'The CSV field `whisper_text` below is Qwen3-ASR output. The WAV links and hash indexes preserve measured files; ASR spelling differences are not automatically audio-quality regressions. These examples include both worse and better scores. Full paired metrics/transcript differences remain in the main report.',''];cache={}
def esc(s):return s.replace('|','\\|').replace('\n',' ')
for phase,title in [('omni','Ming-Omni shared-model check'),('quality','Ming3 quality repeat')]:
 p=e/f'{phase}-audio-index.json'
 if not p.exists():continue
 index=json.loads(p.read_text());groups=collections.defaultdict(dict)
 for x in index:
  prefix,label=x['arm'].rsplit('-',1);groups[(prefix,label[1:],x['sample_id'])][label[0]]=x
 lines += ['## '+title,'',f'[Machine-readable hashes]({phase}-audio-index.json).','', '| Cell / seed / sample | Control | PR | Historical waveform hash match (A/B) |','|---|---|---|---|']
 for (prefix,seed,sample),pair in sorted(groups.items()):
  assert pair.keys()=={'A','B'};cells=[]
  for arm in ['A','B']:
   x=pair[arm];directory=Path(x['file']).parent.parent;csvpath=e/directory/'wer_results.csv'
   if csvpath not in cache:cache[csvpath]={q['id']:q for q in csv.DictReader(csvpath.open())}
   row=cache[csvpath][sample];edits=sum(int(row[k]) for k in ['substitutions','deletions','insertions']);cells.append(f"[WAV]({x['file']})<br>{esc(row['whisper_text'])}<br>{edits} ASR edits")
  hist='N/A (new shared-model check)' if phase=='omni' else '/'.join('yes' if pair[k]['historical_waveform_reproduced_exactly'] else 'no' for k in ['A','B'])
  lines.append(f'| {prefix} / {seed}<br>{sample} | {cells[0]} | {cells[1]} | {hist} |')
 lines += ['']
(e/'audio-examples.md').write_text('\n'.join(lines)+'\n')
p=e/'report.md';s=p.read_text().replace('[selected affected audio with hashes](omni-audio-index.json)','[selected paired recordings](audio-examples.md) ([hash index](omni-audio-index.json))').replace('[Selected affected recordings with hashes](quality-audio-index.json)','[Selected affected recordings](audio-examples.md) ([hash index](quality-audio-index.json))');p.write_text(s)
print('Rendered selected paired WAV/ASR table')
