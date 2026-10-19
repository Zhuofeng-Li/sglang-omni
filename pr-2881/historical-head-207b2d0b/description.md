## Changes

- Add launch/resolve lookahead for eligible whole-prompt ASR prefill; finish bookkeeping before publishing tokens.
- Scope out-of-order request-build admission and admission waits to `async_prefill=True`; retain FIFO admission for Fun-ASR, ArkASR and other opt-out users. Skip repeated waits while prefill admission is blocked.
- Keep the established upstream MRoPE position path; the unvalidated position-reconstruction shortcut has been removed.

**Changed defaults:** Qwen3-ASR on NVIDIA CUDA enables async prefill; the shared scheduler default remains false. Numeric request-build/coalescing defaults are unchanged.

## Paired comparison on current main

Final candidate `207b2d0b3fbd03528525624f0420add1f9213f11` against frozen main `2d5de98cd92b17df7974ac2ef4192b4a99263845`: qualification is pending. The pre-review tables were measured on 2026-10-17/18 against main `8fff1e0e8c99a710afe876d1514209e1157c5502`; their actual heads and complete descriptions are archived in the evidence link. They are not new-head results.

Radix H100 80GB; full SeedTTS EN/ZH; c1/c16/c32/c64; non-streaming and streaming; seeds 42/43 in main(42) → PR(42) → PR(43) → main(43) order, with matched settings and separate quality/failure reporting. No current-head gain is claimed until complete blocks are verified.

### Non-streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | +0.38% |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

Verified c1 non-streaming ABBA block (2026-10-19). Each metric is per scored pass; latency percentiles are not pooled or averaged. The summary averages matched-seed req/s within each language, then takes the geometric mean of the two PR/main ratios. Two seeds do not establish statistical significance.

| Split / seed | Main → PR req/s | Main → PR latency mean / p95 (ms) | First text | Main → PR WER (%) | Main → PR failed / attempted | SIM |
| --- | ---: | --- | --- | ---: | --- | --- |
| EN / 42 | 24.56 → 24.66 | 40.58 / 49.40 → 40.41 / 49.31 | N/A: completed response | 1.2258 → 1.2258 | 0 / 1088 → 0 / 1088 | N/A |
| EN / 43 | 24.55 → 24.65 | 40.60 / 49.63 → 40.42 / 49.36 | N/A: completed response | 1.2258 → 1.2258 | 0 / 1088 → 0 / 1088 | N/A |
| ZH / 42 | 26.94 → 27.14 | 36.93 / 46.86 → 36.71 / 46.72 | N/A: completed response | 0.5933 → 0.5933 | 0 / 2020 → 0 / 2020 | N/A |
| ZH / 43 | 27.14 → 27.13 | 36.72 / 46.73 → 36.73 / 46.73 | N/A: completed response | 0.5933 → 0.5933 | 0 / 2020 → 0 / 2020 | N/A |

### Streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | Pending |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

Detailed req/s, mean/p95 response and first-text latency, corpus WER, SIM (N/A for text-only ASR) and failed/attempted requests will be added after the paired blocks finish.

## Costs

Verified c1 non-streaming block: startup is the two-seed arithmetic mean from server process launch through health-ready, before full-workload warmup. Peak VRAM is the maximum of the 0.5-second samples across each arm's two passes. Live captures are counted after scoring and before service shutdown. Remaining modes/concurrencies are pending.

| c1 non-streaming cost | Main | PR | Delta |
| --- | ---: | ---: | ---: |
| Startup (s) | 75.87 | 75.60 | -0.27 |
| Peak VRAM (GiB) | 70.80 | 70.80 | +0.00 |
| Live captures (seed 42, 43) | 1468, 1468 | 1468, 1468 | +0, +0 |

## Tests

- Review-fix source: **124 Qwen CPU tests, 3 accelerator tests and 122 scheduler / async-decode / Fun-ASR / ArkASR tests passed** on the assigned H100; logs and source identities are in the evidence link.
- `pre-commit run --all-files`: passed. Complete diff versus the frozen main contains no `doc/` or `docs/` changes.
- Existing CI labels: `run-asr-ci` + `run-asr-qwen3-asr-1.7b`. New-head CI and its actual stage/model preflight are being checked; earlier green runs are historical evidence.
- Review-specific validation pending: async-prefill/admission ablation, fixed-seed42 repeats and saved normalized transcript differences; these are separately labeled experiments.
- Performance readiness remains pending until final-source comparisons, costs and current CI are verified.

Developed by an autonomous research agent using [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) in [OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index), with co-author [Kangda Wei (@WeiKangda)](https://github.com/WeiKangda); [qualification and historical evidence](https://github.com/Zhuofeng-Li/sglang-omni/tree/codex/omni-review-evidence-20261019/pr-2881).
