# PR #2881 original H100 review confirmation

Measured 2026-10-19, candidate `e98bcf05e6d27d877cfb134900900ca6fad5d76a` against frozen main `2d5de98cd92b17df7974ac2ef4192b4a99263845`. This preserves the actual measured control and complements the primary two-seed matrix and separate H200 supplement.

Original Radix H100 80GB HBM3, UUID `GPU-e9f60c1d-8856-043c-42cd-47a942a4d8f1`, driver 580.126.20. Same pinned model, dataset, packages, BF16 and cache settings as the original primary matrix; source blobs, packages and YAML are independently checked in `h100-identity-at-start.json`.

24 fresh-service cohorts, 74592 scored requests, zero failures. Every service warmed and scored EN1088 and ZH2020. Admission ablation at C32 uses async-only42, scoped42, scoped43, async-only43; whole-PR repeats at C32/C64 use main42, PR42, PR42, main42 in each mode. Repeated seed42 is not an additional independent seed. SIM is N/A for ASR text.

| Comparison | Concurrency | Mode | Geometric throughput change |
| --- | ---: | --- | ---: |
| admission-ablation | 32 | nonstream | +2.08% |
| admission-ablation | 32 | stream | +1.85% |
| fixed-seed-repeat | 32 | nonstream | +9.87% |
| fixed-seed-repeat | 32 | stream | +9.68% |
| fixed-seed-repeat | 64 | nonstream | +11.72% |
| fixed-seed-repeat | 64 | stream | +11.15% |

For each matched block, average req/s across the two seeds/repetitions within each arm/language, then take the geometric mean of the two language ratios; percentile and WER values remain per pass.

All per-pass response/first-text means and P95s, WER and failed counts are retained in `control/pr2881-h100-priority-summary.json`. Changed normalized transcripts remain in the adjacent differences file. Full raw responses, model/data copies and compiler caches are excluded from this minimal archive.

Coverage completion does not establish merge readiness. Primary-matrix and supplemental first-text/tail-latency regressions and WER changes remain material; do not describe output as equivalent or WER universally flat. Independent review remains required.

## Costs

| Comparison / arm | Mean startup s | Max sampled peak GiB | Successful/live graphs |
| --- | ---: | ---: | --- |
| admission / async_only | 75.78 | 71.80 | [(1468, 1468)] |
| admission / scoped_admission | 75.50 | 71.97 | [(1468, 1468)] |
| repeats / main | 75.30 | 72.16 | [(1468, 1468)] |
| repeats / pr | 75.42 | 71.96 | [(1468, 1468)] |

The H100 allocation remains owned by the original shared batch, which has other consumers. This confirmation does not release or restart that allocation.

Additional independent source/config/GPU/order verification is in `2881-h100-priority-independent-audit.json`; the exact three-method ablation audit is in `pr2881-async-only-identity.json`.
