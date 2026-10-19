## Changes

- Add launch/resolve lookahead for eligible whole-prompt ASR prefill; finish bookkeeping before publishing tokens.
- Scope out-of-order request-build admission and admission waits to `async_prefill=True`; retain main’s FIFO loop for Fun-ASR, ArkASR and other opt-out users, including builds that finish while an earlier request is being admitted. Skip repeated waits while prefill admission is blocked.
- Keep the established upstream MRoPE position path; the unvalidated position-reconstruction shortcut has been removed.

**Changed defaults:** Qwen3-ASR on NVIDIA CUDA enables async prefill; the shared scheduler default remains false. Numeric request-build/coalescing defaults are unchanged.

## Paired comparison on current main

The c1 non-streaming block below was measured on **2026-10-19**; all other final-source blocks remain pending. Pre-review measurements from 2026-10-17/18 used main `8fff1e0e8c99a710afe876d1514209e1157c5502`, and the superseded `207b2d0b` preliminary block is archived separately. Neither archive is final-head evidence.

Candidate `e98bcf05e6d27d877cfb134900900ca6fad5d76a` vs frozen main `2d5de98cd92b17df7974ac2ef4192b4a99263845`.

H100 80GB, SeedTTS EN (1088) / ZH (2020), seeds 42/43; each block runs main(42) → PR(42) → PR(43) → main(43). Throughput and mean latency are arithmetic means across the two seeds. P95, first-text latency and corpus WER retain seed42/43 values. Geometric change uses the ratio of mean req/s for each language, followed by the geometric mean of the two language ratios. Missing or incompletely paired blocks remain Pending. ASR SIM is N/A because the output is text.

The measured c1 point is flat (-0.07%); it does not establish a general throughput benefit. Higher concurrency, streaming, requested ablations and fixed-seed repeats remain pending.

### Non-streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | -0.07% |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

Detailed metrics (main → PR; slash-separated values retain seed42/43):

| c / split | req/s | Mean response ms | P95 response ms | First-text mean ms | First-text P95 ms | WER % | Failed/attempted |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| 1 / EN | 24.480 → 24.485 | 40.70 → 40.71 | 49.49/49.72 → 50.14/49.83 | N/A → N/A | N/A → N/A | 1.2258/1.2258 → 1.2258/1.2258 | 0/2176 → 0/2176 |
| 1 / ZH | 26.811 → 26.765 | 37.13 → 37.23 | 47.24/47.04 → 47.37/47.19 | N/A → N/A | N/A → N/A | 0.5933/0.5933 → 0.5933/0.5933 | 0/4040 → 0/4040 |

### Streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | Pending |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

Detailed metrics (main → PR; slash-separated values retain seed42/43):

| c / split | req/s | Mean response ms | P95 response ms | First-text mean ms | First-text P95 ms | WER % | Failed/attempted |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| Pending | — | — | — | — | — | — | — |

## Costs

Per-cohort startup-to-ready, sampled peak device memory and successful CUDA capture calls (seed42/43; main → PR). Capture calls include segmented prefill captures; they are not unique shape counts. No pooled quantiles or inferred unmeasured costs.

| Mode / c | Startup s | Peak GiB | Successful captures | Live captures after scoring | Capture delta |
| --- | --- | --- | --- | --- | --- |
| nonstream / 1 | 76.10/76.10 → 76.60/75.10 | 70.80/70.79 → 70.80/70.79 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |

## Tests

- Current-head accelerator CI: **769 passed, 15 skipped** on the synthetic merge of this head into main `a1939b97`. The workflow automatically retried once after `test_fast_exit_removes_the_cuda_ipc_reference_file` failed its shared-memory cleanup assertion; the retry passed. The initial failure is retained in the evidence, and its root cause is not asserted. Unit/ASR completion remains pending.
- Review-fix source: **124 CUDA-hidden Qwen cases, 3 accelerator cases, and 250 CUDA-hidden scheduler / async-decode / Fun-ASR / ArkASR cases (8 skipped) passed** on the assigned H100; logs and source identities are in the evidence link.
- `pre-commit run --all-files`: passed. Complete diff versus the frozen main contains no `doc/` or `docs/` changes.
- Existing CI labels: `run-asr-ci` + `run-asr-qwen3-asr-1.7b`. [Current-head Omni CI](https://github.com/sgl-project/sglang-omni/actions/runs/39288752772) (attempt 1): preflight passed and verified `run_asr=true`, `asr_ci_model=qwen3` for `e98bcf05`; unit and ASR completion remains pending. Earlier runs are historical evidence.
- Added a deterministic regression in which a second build finishes during the first admission; main and this head collect both in the same call. The prior review head did not.
- Review-specific validation pending: async-prefill/admission ablation, fixed-seed42 repeats and normalized transcript inspection, separately labeled from standalone main comparisons.
- Performance readiness remains pending until final-source comparisons, costs and current CI are verified.

Developed by an autonomous research agent using [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) in [OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index), with co-author [Kangda Wei (@WeiKangda)](https://github.com/WeiKangda); [qualification and historical evidence](https://github.com/Zhuofeng-Li/sglang-omni/tree/codex/omni-review-evidence-20261019/pr-2881).
