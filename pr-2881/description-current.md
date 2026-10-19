## Changes

- Add launch/resolve lookahead for eligible whole-prompt ASR prefill; finish bookkeeping before publishing tokens.
- Scope out-of-order request-build admission and admission waits to `async_prefill=True`; retain main’s FIFO loop for Fun-ASR, ArkASR and other opt-out users, including builds that finish while an earlier request is being admitted. Skip repeated waits while prefill admission is blocked.
- Keep the established upstream MRoPE position path; the unvalidated position-reconstruction shortcut has been removed.

**Changed defaults:** Qwen3-ASR on NVIDIA CUDA enables async prefill; the shared scheduler default remains false. Numeric request-build/coalescing defaults are unchanged.

## Paired comparison on current main

Measured on **2026-10-19**. All eight primary blocks below are complete; review ablations and repeated fixed-seed checks remain pending. Pre-review 2026-10-17/18 measurements used main `8fff1e0e8c99a710afe876d1514209e1157c5502`; those heads and the superseded `207b2d0b` preliminary block are archived separately and are not final-head results.

Candidate `e98bcf05e6d27d877cfb134900900ca6fad5d76a` vs frozen main `2d5de98cd92b17df7974ac2ef4192b4a99263845`.

H100 80GB, SeedTTS EN (1088) / ZH (2020), seeds 42/43; each block runs main(42) → PR(42) → PR(43) → main(43). Throughput and mean latency are arithmetic means across the two seeds. P95, first-text latency and corpus WER retain seed42/43 values. Geometric change uses the ratio of mean req/s for each language, followed by the geometric mean of the two language ratios. Missing or incompletely paired blocks remain Pending. ASR SIM is N/A because the output is text.

### Non-streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | -0.07% |
| 16 | +5.45% |
| 32 | +7.78% |
| 64 | +8.46% |

Detailed metrics (main → PR; slash-separated values retain seed42/43):

| c / split | req/s | Mean response ms | P95 response ms | First-text mean ms | First-text P95 ms | WER % | Failed/attempted |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| 1 / EN | 24.480 → 24.485 | 40.70 → 40.71 | 49.49/49.72 → 50.14/49.83 | N/A → N/A | N/A → N/A | 1.2258/1.2258 → 1.2258/1.2258 | 0/2176 → 0/2176 |
| 1 / ZH | 26.811 → 26.765 | 37.13 → 37.23 | 47.24/47.04 → 47.37/47.19 | N/A → N/A | N/A → N/A | 0.5933/0.5933 → 0.5933/0.5933 | 0/4040 → 0/4040 |
| 16 / EN | 148.276 → 156.927 | 106.89 → 101.12 | 143.03/139.81 → 131.34/133.90 | N/A → N/A | N/A → N/A | 1.2031/1.2031 → 1.2107/1.2107 | 0/2176 → 0/2176 |
| 16 / ZH | 154.737 → 162.577 | 102.79 → 97.86 | 137.81/137.11 → 129.69/129.38 | N/A → N/A | N/A → N/A | 0.5904/0.5963 → 0.5993/0.6023 | 0/4040 → 0/4040 |
| 32 / EN | 224.604 → 241.493 | 140.09 → 130.49 | 186.38/197.60 → 168.87/206.98 | N/A → N/A | N/A → N/A | 1.2031/1.2182 → 1.2031/1.2031 | 0/2176 → 0/2176 |
| 32 / ZH | 247.929 → 267.841 | 128.16 → 118.43 | 169.72/169.24 → 161.38/157.23 | N/A → N/A | N/A → N/A | 0.5993/0.6173 → 0.6173/0.5963 | 0/4040 → 0/4040 |
| 64 / EN | 291.872 → 318.136 | 211.59 → 196.41 | 288.89/282.87 → 370.26/261.84 | N/A → N/A | N/A → N/A | 1.2107/1.2182 → 1.2107/1.2107 | 0/2176 → 0/2176 |
| 64 / ZH | 303.268 → 327.295 | 209.16 → 186.76 | 295.77/273.06 → 252.62/249.68 | N/A → N/A | N/A → N/A | 0.6143/0.6203 → 0.6293/0.6263 | 0/4040 → 0/4040 |

### Streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | +0.52% |
| 16 | +5.16% |
| 32 | +9.75% |
| 64 | +5.55% |

Detailed metrics (main → PR; slash-separated values retain seed42/43):

| c / split | req/s | Mean response ms | P95 response ms | First-text mean ms | First-text P95 ms | WER % | Failed/attempted |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| 1 / EN | 24.446 → 24.626 | 40.76 → 40.46 | 49.61/49.72 → 49.51/49.51 | 12.20/12.20 → 13.20/12.90 | 14.10/13.40 → 14.90/14.10 | 1.2258/1.2258 → 1.2258/1.2258 | 0/2176 → 0/2176 |
| 1 / ZH | 26.902 → 26.984 | 37.03 → 36.93 | 47.10/46.98 → 46.65/47.24 | 12.00/11.90 → 12.70/13.20 | 13.10/12.70 → 13.50/15.10 | 0.5933/0.5933 → 0.5933/0.5933 | 0/4040 → 0/4040 |
| 16 / EN | 147.775 → 154.450 | 106.47 → 101.56 | 139.63/139.45 → 131.65/135.50 | 56.40/56.70 → 59.60/63.90 | 77.80/80.80 → 80.00/85.00 | 1.2107/1.2031 → 1.2031/1.2031 | 0/2176 → 0/2176 |
| 16 / ZH | 155.357 → 164.365 | 102.23 → 96.75 | 137.99/138.78 → 132.58/127.67 | 59.40/57.30 → 65.30/61.50 | 79.90/78.00 → 83.00/81.50 | 0.5993/0.5933 → 0.5933/0.5993 | 0/4040 → 0/4040 |
| 32 / EN | 224.091 → 246.609 | 139.78 → 128.37 | 179.37/182.18 → 167.03/163.86 | 67.00/71.50 → 71.90/72.10 | 97.30/100.50 → 99.00/99.70 | 1.2107/1.2107 → 1.2182/1.2182 | 0/2176 → 0/2176 |
| 32 / ZH | 239.760 → 262.432 | 132.14 → 120.43 | 171.17/178.48 → 161.04/156.89 | 65.90/67.80 → 69.90/68.90 | 94.50/96.10 → 99.30/97.90 | 0.6233/0.5963 → 0.6053/0.6023 | 0/4040 → 0/4040 |
| 64 / EN | 287.814 → 297.104 | 215.93 → 210.81 | 291.26/282.90 → 420.97/293.96 | 92.40/92.70 → 108.80/108.40 | 179.30/175.20 → 348.70/187.50 | 1.2107/1.2182 → 1.2182/1.2107 | 0/2176 → 0/2176 |
| 64 / ZH | 301.487 → 325.351 | 209.98 → 193.08 | 274.80/290.23 → 259.87/256.21 | 93.70/96.50 → 98.10/98.80 | 133.90/129.90 → 174.90/138.70 | 0.6203/0.6173 → 0.6203/0.6293 | 0/4040 → 0/4040 |

**Observed tradeoffs:** throughput improves at c16/c32/c64, while streaming first-text latency generally increases. At c64 streaming, EN response P95 is 291.26/282.90 → 420.97/293.96 ms and first-text P95 is 179.30/175.20 → 348.70/187.50 ms (seed42/43). Non-streaming c64 EN seed42 P95 also worsens. A c64 seed42 ABBA repeat in both modes has been added; these regressions are retained and this PR is not merge-ready.

Quality is not identical: 88 of 49,728 paired request comparisons change normalized text across the primary conditions (31 improve per-sample WER, 36 worsen, 21 have equal WER). All 29 distinct reference/main/PR triples were inspected: names, homophones, pluralization and small particles; no changed hypothesis is empty. Some corpus WER points worsen in both seeds, including c16 non-streaming EN/ZH and c64 non-streaming ZH. No outliers are removed, and this inspection does not establish the cause or output equivalence.

## Costs

Per-cohort startup-to-ready, sampled peak device memory and successful CUDA capture calls (seed42/43; main → PR). Capture calls include segmented prefill captures; they are not unique shape counts. No pooled quantiles or inferred unmeasured costs.

| Mode / c | Startup s | Peak GiB | Successful captures | Live captures after scoring | Capture delta |
| --- | --- | --- | --- | --- | --- |
| nonstream / 1 | 76.10/76.10 → 76.60/75.10 | 70.80/70.79 → 70.80/70.79 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
| nonstream / 16 | 75.16/76.28 → 75.17/75.75 | 71.61/71.59 → 71.60/71.42 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
| nonstream / 32 | 76.60/76.61 → 76.11/77.67 | 71.64/71.80 → 71.99/71.99 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
| nonstream / 64 | 76.84/75.29 → 75.82/75.60 | 71.94/71.80 → 71.80/72.20 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
| stream / 1 | 76.13/76.59 → 76.10/76.09 | 70.80/70.79 → 70.80/70.79 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
| stream / 16 | 76.08/76.83 → 75.58/77.19 | 71.42/71.60 → 71.76/71.81 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
| stream / 32 | 76.28/76.23 → 76.61/75.84 | 71.81/71.80 → 71.81/71.62 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
| stream / 64 | 77.33/77.12 → 75.81/76.10 | 71.51/71.65 → 71.78/71.98 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |

## Tests

- Current-head CI: **9087 ordinary cases passed (86 skipped); 769 accelerator cases passed (15 skipped)** on the synthetic merge of this head into main `a1939b97`. The workflow automatically retried once after `test_fast_exit_removes_the_cuda_ipc_reference_file` failed its shared-memory cleanup assertion; the retry passed. The initial failure is retained in the evidence, and its root cause is not asserted. Qwen SeedTTS ASR CI has also passed.
- Review-fix source: **124 CUDA-hidden Qwen cases, 3 accelerator cases, and 250 CUDA-hidden scheduler / async-decode / Fun-ASR / ArkASR cases (8 skipped) passed** on the assigned H100; logs and source identities are in the evidence link.
- `pre-commit run --all-files`: passed. Complete diff versus the frozen main contains no `doc/` or `docs/` changes.
- Current-head [Omni CI](https://github.com/sgl-project/sglang-omni/actions/runs/39288752772) passed (attempt 1). Existing labels: `run-asr-ci` + `run-asr-qwen3-asr-1.7b`; preflight selected `run_asr=true`, `asr_ci_model=qwen3`, and stage-2 logs confirm **Qwen/Qwen3-ASR-1.7B**. Unit, accelerator, MOSS-TD prerequisite and Qwen SeedTTS stages passed; unselected stages are not hardware-validation evidence.
- Added a deterministic regression in which a second build finishes during the first admission; main and this head collect both in the same call. The prior review head did not.
- Review-specific validation pending: async-prefill/admission ablation, c32 fixed-seed42 repeats, added c64 seed42 repeats for the measured tail regression, and their normalized transcript comparisons. Primary transcript differences have been inspected and archived separately.
- Performance readiness remains pending until all requested final-source comparisons and review validations, observed tradeoffs, and independent reviewer approval are resolved.

Developed by an autonomous research agent using [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) in [OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index), with co-author [Kangda Wei (@WeiKangda)](https://github.com/WeiKangda); [qualification and historical evidence](https://github.com/Zhuofeng-Li/sglang-omni/tree/codex/omni-review-evidence-20261019/pr-2881).
