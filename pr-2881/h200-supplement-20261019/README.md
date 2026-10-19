# PR #2881: independent H200 supplementary qualification

Final candidate `e98bcf05e6d27d877cfb134900900ca6fad5d76a`; frozen upstream control `2d5de98cd92b17df7974ac2ef4192b4a99263845`. Measured 2026-10-19. These measurements complement the separately archived H100 primary matrix and do not replace H100 tail-latency confirmation or relabel the control as latest upstream main.

One Radix H200 (GPU UUID `GPU-2396c1ff-41ff-385f-30fe-0272d99c5d6c`), driver 595.71.05, image `docker.io/lmsysorg/sglang@sha256:06e4f2ed21afde4ff513cda65070124e727ba23ccaeff7712b8c40e1097d611f`. No CPU quota/affinity override; both arms use the same default shared scheduling. Exact package, sample-order and source fingerprints are retained in `preflight.json`; GPU/container settings are in `runtime-hardware.txt`.

Four smoke cohorts and 24 measured fresh-service cohorts completed. Every measured cohort warms up and scores the complete EN 1088 / ZH 2020 splits. Model `Qwen/Qwen3-ASR-1.7B@7278e1e70fe206f11671096ffdd38061171dd6e5`; dataset `zhaochenyang20/seed-tts-eval-arrow@27f4c1adee83b5b29b7c4b375f6b976324bda308`. Generated YAML, launch/config identities, failed/attempted counts, WER, throughput/latency, startup, peak memory and graph counters are retained per cohort. ASR SIM is N/A because output is text.

Admission ablation uses async-only(42), scoped-admission(42), scoped-admission(43), async-only(43) at C32 in each mode. The async-only arm restores frozen-main input/build admission methods while retaining final async prefill; both arms retain upstream MRoPE. Fixed-seed repeats use main(42), PR(42), PR(42), main(42), separately at C32/C64 and in both modes. They test repeatability at one fixed seed and are not additional independent random seeds.

## Matched-block throughput

| Comparison | Concurrency | Mode | EN/ZH geometric throughput change |
| --- | ---: | --- | ---: |
| admission-ablation | 32 | nonstream | +2.57% |
| admission-ablation | 32 | stream | -0.23% |
| fixed-seed-repeat | 32 | nonstream | +3.82% |
| fixed-seed-repeat | 32 | stream | +3.88% |
| fixed-seed-repeat | 64 | nonstream | +5.77% |
| fixed-seed-repeat | 64 | stream | +3.97% |

For each matched block, average req/s across the two seeds/repetitions within each arm/language, then take the geometric mean of the two language ratios; percentile and WER values remain per pass.

Complete metrics, including negative changes and per-pass percentile/WER values, are in `summary.json`. Changed normalized transcripts and WER directions are in `transcript-differences.json`. Full raw sample responses, compiler caches, model/data copies and complete startup logs remain outside this minimal archive.

Coverage completion alone does not establish merge readiness. Preserve primary and supplementary first-text/tail-latency or WER regressions, and review them separately from throughput. Required independent approval and remaining original H100 review qualification are separate gates.

## Observed tradeoffs

Not merge-ready: first-text latency increases persist; C64 streaming EN P95 worsens in one H200 repeat and improves in the other, so the original H100 regression cannot be dismissed. Admission-only streaming throughput change is near zero/negative. Await original H100 confirmation and independent reviewer approval.

Across the main/PR repeats, 72 paired utterances change normalized output: 29 improve WER, 29 worsen it and 14 keep equal WER. Admission ablation adds 27 changes (12 improve, 10 worsen, 5 equal). All 31 distinct changed triples were inspected; no changed hypothesis is empty. Numerical cause and audio-truncation absence are not established.

C64 streaming EN response P95 is 407.38/459.54 → 447.95/423.35 ms; first-text P95 is 314.90/336.30 → 338.70/338.40 ms. This preserves both repeat directions and does not average percentiles.

## Supplementary costs

| Comparison | Mean startup s, left → right | Max peak GiB, left → right | Successful/live captures per service |
| --- | --- | --- | --- |
| Async only → scoped admission | 104.37 → 103.30 | 132.38 → 132.53 | 1468 / 1468 on both arms; delta 0 |
| Main → PR repeats | 102.07 → 103.17 | 132.81 → 132.80 | 1468 / 1468 on both arms; delta 0 |

Startup averages cover both modes: four services per ablation arm, eight per main/PR repeat arm. Peaks are maximum sampled device usage. All 24 formal cohorts have 1468 successful captures and 1468 live captures after scoring. Full per-service costs remain in result files.

The dedicated H200 assignment was released only after off-node checksum/count verification and no remaining compute consumers; `monitor-state.json` and `release-response.txt` record confirmation. The separate H100 assignment still serves the original queue and was not released.
