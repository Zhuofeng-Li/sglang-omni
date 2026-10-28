"""Export completed shared-model evidence only; never run or modify a benchmark."""
from pathlib import Path
import hashlib,json,shutil,tarfile
r=Path(__file__).resolve().parent
a=json.loads((r/'omni-analysis.json').read_text());assert a['completed_arms']==32 and len(a['paired_cells'])==8
assert sum(x['speed']['completed_requests'] for x in a['arms'])==1024
assert all(x['speed']['failed_requests']==0 and x['startup_rng_capture_verified'] for x in a['arms'])
assert all(x['speed']['max_token_hits']==0 for x in a['arms'])
assert all([x['serving_graph_coverage'][k]['captures'] for k in ['sglang_ar','ming_tts_tail','streaming_vae']]==[4,4,1] for x in a['arms'])
assert sum(q['same_wav'] for x in a['paired_cells'] if x['concurrency']==1 for q in x['pairs'])==256
e=r.parent/'evidence-repo/evidence/ming-review-20261028';e.mkdir(exist_ok=True)
shutil.copy2(r/'omni-analysis.json',e/'omni-analysis.json')
selected={
 ('omni-en-c8-full-A43','common_voice_en_15265-common_voice_en_15266'),
 ('omni-en-c8-full-B43','common_voice_en_15265-common_voice_en_15266'),
 ('omni-en-c8-stream-A42','common_voice_en_15734837-common_voice_en_15734838'),
 ('omni-en-c8-stream-B42','common_voice_en_15734837-common_voice_en_15734838'),
}
# Add observed Chinese differences only after those waveforms are included in final backup.
extra=r/'omni-selected-audio.json'
if extra.exists():selected.update(tuple(x) for x in json.loads(extra.read_text()))
root_files={'source-receipts.json','runtime-freeze.txt','runtime-image.json','seed-protocol.json','run_ming_omni_arm.py','run_omni_queue.py','omni-plan.json','omni-queue-status.json','omni-observe/sitecustomize.py'}
arm_files={'result.json','config.json','command.json','server-config.yaml','resolved-pipeline.json','runtime.json','graphs.jsonl','replays.jsonl','audio_sha256.json','speaker_similarity.json','container-command.json','output/wer_results.csv','output/wer_results.json','output/generated.json'}
index=[]
with tarfile.open(r/'parallel-omni/latest-backup.tar.gz') as t:
 state=json.load(t.extractfile('omni-queue-status.json'));assert state['stage']=='complete' and len(state['completed'])==32
 for member in t.getmembers():
  if not member.isfile():continue
  p=Path(member.name);assert not p.is_absolute() and '..' not in p.parts
  include=member.name in root_files
  if len(p.parts)>2 and p.parts[0]=='omni-results':
   include=Path(*p.parts[2:]).as_posix() in arm_files
   if len(p.parts)==5 and p.parts[2:4]==('output','audio'):
    include=(p.parts[1],p.stem) in selected
    if include:
     expected=json.load(t.extractfile(f'omni-results/{p.parts[1]}/audio_sha256.json'))[p.stem];payload=t.extractfile(member).read();assert hashlib.sha256(payload).hexdigest()==expected;index.append({'arm':p.parts[1],'sample_id':p.stem,'sha256':expected,'file':'omni/'+member.name})
  if include:
   target=e/'omni'/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(t.extractfile(member).read())
assert len(index)==len(selected),(len(index),len(selected))
(e/'omni-audio-index.json').write_text(json.dumps(index,indent=2))
for p in ['analyze_omni.py','current-preflight-lines.json','unit-status.json','unit.log','unit-skip-analysis.json','final-attribution-ast-proof.json']:
 shutil.copy2(r/p,e/p)
shutil.copy2(r/'parallel-omni/backup-status.json',e/'omni-backup-receipt.json')
lines=['## #3217 requested shared-model validation','',
 '**Complete bounded shared-model check:** 32 arms / 1,024 formal requests, zero failures or output-budget hits. First 32 EN and ZH SeedTTS samples; c1/c8; both modes; startup seeds 42/43 ABBA. Control is #3190 `d57f2e970df64266b04e09bf716ba0ecc2342eca` (tree64a386f4); candidate is #3217 `96957d08e9dcd260005f5e92b9d13e90c544bbcf` (treea41d246d), on one H200 `GPU-da0d9c21-eb80-f5c6-c12c-bfc5bcb9f207`. This dependency ablation does not establish an independent-main Tiny gain.',
 '', 'Checkpoint `inclusionAI/Ming-omni-tts-16.8B-A3B@2efcd28d04f83b1bd471af639b4210c9ecf2cd33`; provided `examples/configs/ming_omni_tts.yaml`, max-running8 / graph buckets1,2,4,8 / output budget256. Request seeds are omitted because the native API rejects them; startup RNG and engine seed42/43 are verified from actual CPU/CUDA seeds at capture. Concurrent requests are not individually deterministic. ASR and fixed Dense CAM++ score every output. Full-response AudioVAE remains compact eager; AR and acoustic-tail graph serving replays are verified in every arm, with AudioVAE serving replays additionally required in every streaming arm.',
 '', '| Language | c | Stream | WER% control → PR | SIM control → PR | Edits control/PR at42;43 | Failed/attempted |', '|---|---:|:---:|---:|---:|---|---:|']
for x in a['paired_cells']:
 aa,bb=x['mean']['A'],x['mean']['B'];ed='; '.join(f"{q['control_edits']}/{q['candidate_edits']}" for q in x['pairs'])
 lines.append(f"| {x['language'].upper()} | {x['concurrency']} | {str(x['stream']).lower()} | {aa['wer_percent']:.4f} → {bb['wer_percent']:.4f} | {aa['sim']:.6f} → {bb['sim']:.6f} | {ed} | 0/128 |")
lines += ['', 'All 256 c1 paired WAV comparisons are hash-identical. The ZH streaming seed 43 WER difference is one ASR edit on identical WAV `10002698-00000106` (发展生/发展商), demonstrating scoring variability without an audio change. Means are arithmetic means of the two seed corpus scores. Native concurrency8 scheduling can assign global FlowLoss noise differently despite the same startup seed. Differences remain visible; no non-inferiority threshold or deterministic per-request equivalence is asserted. One ZH c8 streaming control output (seed 43,10002539-00000054) transcribed as 嗯 and has 16 edits versus 0 in the candidate; its paired recordings are retained. Zero failed requests means transport/model completion, not zero word errors or uniformly good quality. [All per-seed results and paired transcript differences](omni-analysis.json); [selected affected audio with hashes](omni-audio-index.json).', '', 'Every arm captured 4 AR + 4 acoustic-tail + 1 streaming AudioVAE graphs (the VAE graph is prepared at startup in both modes). Non-streaming requests do not replay the streaming VAE graph. Cost values below are observed subset-run ranges, not independent Tiny costs or a speedup claim.']
for arm in ['omni-control','omni-candidate']:
 xs=[x for x in a['arms'] if x['config']['arm']==arm];s=[x['costs']['startup_to_ready_s'] for x in xs];v=[x['costs']['peak_tts_device_gib'] for x in xs]
 assert all(x['costs']['successful_tts_captures']==9 for x in xs)
 lines.append(f"- {arm}: startup {min(s):.2f}–{max(s):.2f}s; peak device {min(v):.3f}–{max(v):.3f}GiB; 9 captures/arm, graph-count increment0.")
lines += ['', 'Two operator-input preflight failures (unsupported request seed, then generic 2048 budget exceeding the provided 256 cap) occurred during warmup before formal requests and were retained separately. Production request guards and regression assertions were kept.', '', '#3217 remains Draft: dependency landing and the independent full Tiny matrix/quality/cost qualification are still pending. This complete shared-model subset fills only the specific cross-model review request.', '']
p=e/'report.md';s=p.read_text().replace('#3217 shared-model completion, prerequisite landing,','#3217 prerequisite landing,');start=s.index('## #3217 requested shared-model validation');end=s.index('## Remaining gates',start);p.write_text(s[:start]+'\n'.join(lines)+'\n'+s[end:])
print('Exported complete MingOmni raw results/config/graph proof and selected audio; original PR publication still required')
