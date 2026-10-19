"""Prepare requested EN-only MOSS tables from complete audited ABBA blocks."""
import json
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]


def slash(values, precision=3):
    return "/".join(f"{value:.{precision}f}" for value in values)


def render(audit):
    lines = [
        f"Prepared candidate `{audit['candidate']}` vs frozen main `{audit['frozen_main']}`.",
        "",
        "Requested c1/c64 EN-only backfill: full 1088 requests per cohort, seeds 42/43 in main(42) → PR(42) → PR(43) → main(43) order. "
        "The req/s change uses arithmetic means across seeds. Slash-separated values retain seed42/43; percentiles are not pooled. "
        "Each displayed block requires completed generation, full WER/SIM scoring, matched settings/order, the assigned GPU and audited ABBA intervals. "
        "The bilingual geometric summary is N/A for this EN-only workload; historical c16 remains separate with its original source/date.",
        "",
    ]
    metrics = []
    cost_lines = ["Per-cohort costs (seed42/43; main → PR). Startup is launch-to-health-ready, peak memory is sampled every 0.5 s, and graph counts are successful capture events rather than unique shapes or post-shutdown live objects.", "", "| Mode / c | Startup s | Peak GiB | Successful captures | Capture delta |", "| --- | --- | --- | --- | --- |"]
    for mode, title in [("nonstream", "Non-streaming"), ("stream", "Streaming")]:
        lines += [f"### {title}", "", "| Concurrency | EN/ZH geometric throughput change |", "| ---: | --- |", "| 1 | N/A: EN-only workload |", "| 16 | N/A: historical EN-only workload |", "| 32 | N/A: outside requested EN-only backfill |", "| 64 | N/A: EN-only workload |", "", "| c | EN req/s (main → PR) | Change | Mean response s | P95 response s | First audio mean s | First audio P95 s | WER % | SIM ×100 | Failed/attempted |", "| ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |"]
        for concurrency in [1, 64]:
            block = next(b for b in audit["blocks"] if b["mode"] == mode and b["concurrency"] == concurrency)
            if block["status"] != "verified":
                lines.append(f"| {concurrency} | Pending | — | — | — | — | — | — | — | — |")
                continue
            arms = {}
            for arm in ["main", "pr"]:
                rows = [next(r for r in audit["generations"] if r["name"] == f"pr2859-c{concurrency}-{mode}-{arm}-seed{seed}") for seed in [42, 43]]
                assert all(r["status"] == "verified" and r["quality"] == "verified" for r in rows)
                arms[arm] = dict(
                    req_s=mean(r["speed"]["summary"]["throughput_qps"] for r in rows),
                    mean_latency_s=slash([r["speed"]["summary"]["latency_mean_s"] for r in rows]),
                    p95_latency_s=slash([r["speed"]["summary"]["latency_p95_s"] for r in rows]),
                    first_audio_mean_s=slash([r["speed"]["summary"]["audio_ttfp_mean_s"] for r in rows], 4) if mode == "stream" else "N/A",
                    first_audio_p95_s=slash([r["speed"]["summary"]["audio_ttfp_p95_s"] for r in rows], 4) if mode == "stream" else "N/A",
                    wer_percent=slash([100 * r["wer"]["summary"]["wer_corpus"] for r in rows], 4),
                    sim_percent=slash([100 * r["similarity"]["summary"]["speaker_similarity_mean"] for r in rows], 4),
                    failed=sum(r["speed"]["summary"]["failed_requests"] for r in rows),
                    attempted=sum(r["speed"]["summary"]["total_requests"] for r in rows),
                    startup_s=slash([r["costs"]["startup_seconds"] for r in rows], 2),
                    peak_gib=slash([r["result"]["peak_mib"] / 1024 for r in rows], 2),
                    captures=[r["costs"]["successful_captures"] for r in rows],
                    finish_reason_observed=[r["speed"]["summary"]["finish_reason_observed"] for r in rows],
                    max_token_hits=[r["speed"]["summary"]["max_token_hits"] for r in rows],
                    evidence=[r["name"] for r in rows],
                )
            a, b = arms["main"], arms["pr"]
            change = 100 * (b["req_s"] / a["req_s"] - 1)
            paired = lambda key: f"{a[key]} → {b[key]}"
            cells = [f"{a['req_s']:.3f} → {b['req_s']:.3f}", f"{change:+.2f}%", *[paired(k) for k in ["mean_latency_s", "p95_latency_s", "first_audio_mean_s", "first_audio_p95_s", "wer_percent", "sim_percent"]], f"{a['failed']}/{a['attempted']} → {b['failed']}/{b['attempted']}"]
            lines.append(f"| {concurrency} | " + " | ".join(cells) + " |")
            sequence = lambda xs: "/".join(str(x) for x in xs)
            cost_lines.append(f"| {mode} / {concurrency} | {paired('startup_s')} | {paired('peak_gib')} | {sequence(a['captures'])} → {sequence(b['captures'])} | {sequence([right-left for left,right in zip(a['captures'],b['captures'])])} |")
            metrics.append(dict(mode=mode, concurrency=concurrency, throughput_change_percent=change, arms=arms))
        lines.append("")
    if not metrics:
        cost_lines.append("| Pending | — | — | — | — |")
    lines.append("Token-cap hits and finish-reason observation counts are retained in the per-seed JSON. Missing observed finish reasons cannot establish absence of truncation. No outliers are removed.")
    target = ROOT / "rendered"
    target.mkdir(exist_ok=True)
    (target / "pr-2859-comparison.md").write_text("\n".join(lines) + "\n")
    (target / "pr-2859-costs.md").write_text("\n".join(cost_lines) + "\n")
    (target / "pr-2859-metrics.json").write_text(json.dumps(dict(candidate=audit["candidate"], frozen_main=audit["frozen_main"], metrics=metrics), indent=2) + "\n")
    return len(metrics)


if __name__ == "__main__":
    audit = json.loads((ROOT / "performance-audit.json").read_text())
    print(json.dumps({"2859": render(audit["prs"]["2859"])}))
