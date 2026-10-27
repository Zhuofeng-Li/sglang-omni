"""Summarize saved native benchmark records without changing measurements."""
from pathlib import Path
import argparse
import json
import statistics
import tarfile


def percentile(values, quantile):
    ordered = sorted(values)
    if not ordered:
        return None
    position = (len(ordered) - 1) * quantile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def summarize(report):
    rows = report['per_request']
    success = [row for row in rows if row['is_success']]
    result = {'attempted': len(rows), 'failed': len(rows) - len(success),
              'native_summary': report['summary']}
    for field in ['latency_s', 'audio_ttfp_s', 'audio_duration_s', 'max_playback_underrun_s']:
        values = [row[field] for row in success if row.get(field) is not None]
        result[field] = {'count': len(values), 'mean': statistics.mean(values) if values else None,
                         'p95': percentile(values, .95), 'max': max(values) if values else None}
    scored = [row['max_playback_underrun_s'] for row in success
              if row.get('max_playback_underrun_s') is not None]
    result.update(continuity_scored=len(scored), continuity_na=len(success) - len(scored),
                  positive_underrun=sum(value > 0 for value in scored),
                  total_completion_tokens=sum(row.get('completion_tokens') or 0 for row in success))
    result['continuity_percent'] = {str(ms): 100 * sum(value <= ms / 1000 for value in scored) / len(scored)
                                    if scored else None for ms in [50, 100, 200]}
    result['finish_reasons'] = {reason: sum(row.get('finish_reason') == reason for row in rows)
                                for reason in sorted({row.get('finish_reason', '') for row in rows})}
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('archive', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = {}
    with tarfile.open(args.archive, 'r:gz') as archive:
        for member in archive.getmembers():
            if member.name.startswith('metrics-') and member.name.endswith('/speed_results.json'):
                report = json.load(archive.extractfile(member))
                data[str(Path(member.name).parent)] = summarize(report)
    args.output.write_text(json.dumps(data, indent=2) + '\n')
    print(f'{len(data)} completed blocks summarized')
