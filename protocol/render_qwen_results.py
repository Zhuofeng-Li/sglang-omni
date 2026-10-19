"""Render only complete, audited ABBA blocks; never publish or infer readiness."""
import json
import math
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]


def pair(left, right, precision=3):
    return f"{left:.{precision}f} → {right:.{precision}f}"


def seed_values(rows, getter, scale=1, precision=2):
    return "/".join(f"{scale * getter(row):.{precision}f}" for row in rows)


def render(number, audit):
    lines = [
        f"Candidate `{audit['candidate']}` vs frozen main `{audit['frozen_main']}`.",
        "",
        "H100 80GB, SeedTTS EN (1088) / ZH (2020), seeds 42/43; each block runs main(42) → PR(42) → PR(43) → main(43). "
        "Throughput and mean latency are arithmetic means across the two seeds. P95, first-text latency and corpus WER retain seed42/43 values. "
        "Geometric change uses the ratio of mean req/s for each language, followed by the geometric mean of the two language ratios. "
        "Missing or incompletely paired blocks remain Pending. ASR SIM is N/A because the output is text.",
        "",
    ]
    metrics = []
    costs = []
    for mode, title in [("nonstream", "Non-streaming"), ("stream", "Streaming")]:
        lines += [f"### {title}", "", "| Concurrency | EN/ZH geometric throughput change |", "| ---: | ---: |"]
        verified = []
        for concurrency in [1, 16, 32, 64]:
            block = next(b for b in audit["blocks"] if b["mode"] == mode and b["concurrency"] == concurrency)
            if block["status"] != "verified":
                lines.append(f"| {concurrency} | Pending |")
                continue
            verified.append(concurrency)
            rows = [r for r in audit["cells"] if r["mode"] == mode and r["concurrency"] == concurrency]
            assert len(rows) == 8 and all(r["status"] == "verified" for r in rows)
            ratios = []
            for language in ["en", "zh"]:
                arms = {}
                for arm in ["main", "pr"]:
                    seeds = sorted((r for r in rows if r["language"] == language and r["arm"] == arm), key=lambda r: r["seed"])
                    assert [r["seed"] for r in seeds] == [42, 43]
                    assert all(r["metrics"]["summary"]["skipped"] == 0 for r in seeds)
                    arms[arm] = {
                        "req_s": mean(r["metrics"]["speed"]["asr_throughput_samples_per_s"] for r in seeds),
                        "mean_latency_ms": 1000 * mean(r["metrics"]["summary"]["latency_mean_s"] for r in seeds),
                        "p95_ms": seed_values(seeds, lambda r: r["metrics"]["summary"]["latency_p95_s"], 1000),
                        "wer_percent": seed_values(seeds, lambda r: r["metrics"]["summary"]["wer_corpus"], 100, 4),
                        "first_text_mean_ms": seed_values(seeds, lambda r: r["metrics"]["speed"]["text_ttft_mean_s"], 1000) if mode == "stream" else "N/A",
                        "first_text_p95_ms": seed_values(seeds, lambda r: r["metrics"]["speed"]["text_ttft_p95_s"], 1000) if mode == "stream" else "N/A",
                        "failed": sum(r["metrics"]["summary"]["skipped"] for r in seeds),
                        "attempted": sum(r["metrics"]["summary"]["total_samples"] for r in seeds),
                        "evidence": [r["evidence"] for r in seeds],
                    }
                ratio = arms["pr"]["req_s"] / arms["main"]["req_s"]
                assert math.isfinite(ratio) and ratio > 0
                ratios.append(ratio)
                metrics.append(dict(mode=mode, concurrency=concurrency, language=language, arms=arms))
            change = 100 * (math.sqrt(math.prod(ratios)) - 1)
            lines.append(f"| {concurrency} | {change:+.2f}% |")
        lines += ["", "Detailed metrics (main → PR; slash-separated values retain seed42/43):", "", "| c / split | req/s | Mean response ms | P95 response ms | First-text mean ms | First-text P95 ms | WER % | Failed/attempted |", "| --- | ---: | ---: | --- | --- | --- | --- | --- |"]
        for row in [m for m in metrics if m["mode"] == mode]:
            a, b = row["arms"]["main"], row["arms"]["pr"]
            lines.append(f"| {row['concurrency']} / {row['language'].upper()} | {pair(a['req_s'], b['req_s'])} | {pair(a['mean_latency_ms'], b['mean_latency_ms'], 2)} | {a['p95_ms']} → {b['p95_ms']} | {a['first_text_mean_ms']} → {b['first_text_mean_ms']} | {a['first_text_p95_ms']} → {b['first_text_p95_ms']} | {a['wer_percent']} → {b['wer_percent']} | {a['failed']}/{a['attempted']} → {b['failed']}/{b['attempted']} |")
        if not verified:
            lines.append("| Pending | — | — | — | — | — | — | — |")
        lines.append("")
        for concurrency in verified:
            # EN and ZH share each service launch; count each launch once.
            rows = [r for r in audit["cells"] if r["mode"] == mode and r["concurrency"] == concurrency and r["language"] == "en"]
            arms = {}
            for arm in ["main", "pr"]:
                seeds = sorted((r for r in rows if r["arm"] == arm), key=lambda r: r["seed"])
                arms[arm] = dict(
                    startup_s=seed_values(seeds, lambda r: r["costs"]["startup_seconds"]),
                    peak_gib=seed_values(seeds, lambda r: r["costs"]["peak_memory_mib"] / 1024),
                    successful_captures=[r["costs"]["graphs_after_scoring"]["successful_captures"] for r in seeds],
                    live_captures=[r["costs"]["graphs_after_scoring"]["live_captures"] for r in seeds],
                )
            costs.append(dict(mode=mode, concurrency=concurrency, arms=arms))
    comparison = "\n".join(lines).rstrip() + "\n"
    cost_lines = ["Per-cohort startup-to-ready, sampled peak device memory and successful CUDA capture calls (seed42/43; main → PR). Capture calls include segmented prefill captures; they are not unique shape counts. No pooled quantiles or inferred unmeasured costs.", "", "| Mode / c | Startup s | Peak GiB | Successful captures | Live captures after scoring | Capture delta |", "| --- | --- | --- | --- | --- | --- |"]
    for row in costs:
        a, b = row["arms"]["main"], row["arms"]["pr"]
        seq = lambda xs: "/".join(str(x) for x in xs)
        delta = [right - left for left, right in zip(a["successful_captures"], b["successful_captures"])]
        cost_lines.append(f"| {row['mode']} / {row['concurrency']} | {a['startup_s']} → {b['startup_s']} | {a['peak_gib']} → {b['peak_gib']} | {seq(a['successful_captures'])} → {seq(b['successful_captures'])} | {seq(a['live_captures'])} → {seq(b['live_captures'])} | {seq(delta)} |")
    if not costs:
        cost_lines.append("| Pending | — | — | — | — | — |")
    target = ROOT / "rendered"
    target.mkdir(exist_ok=True)
    (target / f"pr-{number}-comparison.md").write_text(comparison)
    (target / f"pr-{number}-costs.md").write_text("\n".join(cost_lines) + "\n")
    (target / f"pr-{number}-metrics.json").write_text(json.dumps(dict(candidate=audit["candidate"], frozen_main=audit["frozen_main"], metrics=metrics, costs=costs), indent=2) + "\n")
    return len(metrics)


if __name__ == "__main__":
    audit = json.loads((ROOT / "performance-audit.json").read_text())
    print(json.dumps({number: render(number, audit["prs"][number]) for number in ["2880", "2881", "2882"]}))
