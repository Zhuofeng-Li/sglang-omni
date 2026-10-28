from pathlib import Path
import csv, datetime, io, json, tarfile
root = Path(__file__).resolve().parent
archive = root.parent / 'current-results-backup.tar.gz'
output = []
with tarfile.open(archive) as source:
    for language, concurrency in [('en',16),('zh',1)]:
        for seed in [42,43]:
            arms = {}
            for label in ['A','B']:
                identity=f'lifetime-corrected-{language}-c{concurrency}-{label}{seed}'
                payload=source.extractfile(f'results/{identity}/output/wer_results.csv').read().decode()
                arms[label]={row['id']: row for row in csv.DictReader(io.StringIO(payload))}
            assert arms['A'].keys()==arms['B'].keys()
            totals={'reference_units':0,'control_errors':0,'candidate_errors':0,'worse_samples':0,'better_samples':0,'unchanged_error_samples':0}
            differences=[]
            for identity,a in arms['A'].items():
                b=arms['B'][identity];assert a['target_text']==b['target_text']
                counts=[sum(int(row[k]) for k in ['substitutions','deletions','insertions']) for row in [a,b]]
                denominators=[sum(int(row[k]) for k in ['hits','substitutions','deletions']) for row in [a,b]]
                assert denominators[0]==denominators[1]
                totals['reference_units']+=denominators[0];totals['control_errors']+=counts[0];totals['candidate_errors']+=counts[1]
                delta=counts[1]-counts[0];totals['worse_samples' if delta>0 else 'better_samples' if delta<0 else 'unchanged_error_samples']+=1
                if a['whisper_text']!=b['whisper_text']:
                    differences.append({'id':identity,'target':a['target_text'],'control_transcript':a['whisper_text'],'candidate_transcript':b['whisper_text'],'control_errors':counts[0],'candidate_errors':counts[1],'error_delta':delta,'control_duration':a['audio_duration_s'],'candidate_duration':b['audio_duration_s']})
            totals['control_wer_percent']=100*totals['control_errors']/totals['reference_units'];totals['candidate_wer_percent']=100*totals['candidate_errors']/totals['reference_units'];totals['delta_pp']=totals['candidate_wer_percent']-totals['control_wer_percent']
            differences.sort(key=lambda x:(-x['error_delta'],x['id']))
            cell={'language':language,'concurrency':concurrency,'seed':seed,'samples':len(arms['A']),'totals':totals,'transcript_differences':differences}
            output.append(cell)
report={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'source_archive':str(archive),'control':'0d6a414e5e15c996900620d263143c89e0dd8acd','candidate':'3f8593f4cae19fe1c71e929a854bdc03b2c185e6','scope':'Historical affected cells; existing ASR transcripts and edit counts. No new audio generation, listening or non-inferiority claim. Original WAV hashes retained; old node audio unavailable after release.','cells':output}
(root/'paired-error-inspection.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
for cell in output:
 print(json.dumps({k:v for k,v in cell.items() if k!='transcript_differences'},ensure_ascii=False));print(json.dumps(cell['transcript_differences'][:2],ensure_ascii=False))
