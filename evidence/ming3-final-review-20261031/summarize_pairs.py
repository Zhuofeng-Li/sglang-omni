"""Summarize only completed four-arm blocks; never publish incomplete pairs."""
from pathlib import Path
import hashlib
import json
import statistics
import subprocess
import sys
import tarfile

root = Path(__file__).resolve().parent
archive_path = Path(sys.argv[1]) if len(sys.argv) > 1 else root / "latest-results.tar.gz"
subprocess.run([sys.executable, str(root / "verify_completed.py"), str(archive_path)],
               check=True, stdout=subprocess.DEVNULL)
verified = json.loads((root / "completed-arm-verification.json").read_text())
assert verified["source_archive_sha256"] == hashlib.sha256(archive_path.read_bytes()).hexdigest()
plan = json.loads((root / "measurement-plan.json").read_text())
groups = {}
for cell in plan:
    key = (cell["comparison"], cell["language"], cell["concurrency"])
    groups.setdefault(key, []).append(cell)
checked = {row["arm"]: row for row in verified["checked"]}
output = []
with tarfile.open(archive_path) as archive:
    for (comparison, language, concurrency), cells in groups.items():
        row = {"comparison": comparison, "language": language, "concurrency": concurrency,
               "completed": sum(c["id"] in checked for c in cells), "expected": 4}
        assert [c["label"] for c in cells] == ["A42", "B42", "B43", "A43"]
        if row["completed"] != 4:
            row["status"] = "Pending; no paired aggregate claimed"
            output.append(row)
            continue
        values = {c["label"]: json.load(archive.extractfile("results/" + c["id"] + "/result.json"))
                  for c in cells}
        sides = {}
        for side in ["A", "B"]:
            arms = [values[side + str(seed)] for seed in [42, 43]]
            def mean(section, key):
                return statistics.mean(a[section][key] for a in arms)
            metrics = {
                "source_commits": sorted({checked[a["config"]["id"]]["actual_source_commit"] for a in arms}),
                "stream": arms[0]["config"]["stream"],
                "throughput_qps_seed_mean": mean("speed", "throughput_qps"),
                "latency_mean_s_seed_mean": mean("speed", "latency_mean_s"),
                "latency_p95_s_seed_range": [min(a["speed"]["latency_p95_s"] for a in arms),
                                             max(a["speed"]["latency_p95_s"] for a in arms)],
                "wer_percent_seed_mean": 100 * mean("wer", "wer_corpus"),
                "sim_seed_mean": mean("speaker_sim", "mean"),
                "audio_duration_s_seed_mean": mean("wer", "audio_duration_mean_s"),
                "output_tokens_total_by_seed": {a["config"]["seed"]: a["speed"]["output_tokens_total"] for a in arms},
                "requests_total": sum(a["speed"]["total_requests"] for a in arms),
                "failed_total": sum(a["speed"]["failed_requests"] for a in arms),
                "startup_s_seed_mean": mean("costs", "startup_to_ready_s"),
                "peak_device_gib_by_seed": {a["config"]["seed"]: a["costs"]["peak_tts_device_gib"] for a in arms},
                "capture_events_by_seed": {a["config"]["seed"]: a["costs"]["successful_tts_captures"] for a in arms},
            }
            # Preserve all native first-packet fields without guessing their names.
            metrics["first_packet_metrics_by_seed"] = {
                a["config"]["seed"]: {k: v for k, v in a["speed"].items()
                                        if any(token in k for token in ["ttfa", "ttfp", "first_audio", "first_chunk", "ttft"])}
                for a in arms
            }
            sides[side] = metrics
        a, b = sides["A"], sides["B"]
        row.update(status="Complete block; descriptive differences, no quality acceptance threshold assumed",
                   sides=sides,
                   throughput_change_percent=100 * (b["throughput_qps_seed_mean"] / a["throughput_qps_seed_mean"] - 1),
                   wer_change_percentage_points=b["wer_percent_seed_mean"] - a["wer_percent_seed_mean"],
                   sim_change=b["sim_seed_mean"] - a["sim_seed_mean"],
                   audio_duration_change_percent=100 * (b["audio_duration_s_seed_mean"] / a["audio_duration_s_seed_mean"] - 1))
        output.append(row)
result = {"archive_sha256": verified["source_archive_sha256"], "blocks": output,
          "protocol": "Seed means for mean metrics; p95 retained as seed range. ABBA A42 B42 B43 A43. EN c16 and ZH c1 are different cells and must not be combined into an EN/ZH geometric throughput number.",
          "limitations": verified["limitations"]}
(root / "paired-block-summary.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps(result))
