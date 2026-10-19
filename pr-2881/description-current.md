## Changes

- Add launch/resolve lookahead for eligible whole-prompt ASR prefill; finish bookkeeping before publishing tokens.
- Scope out-of-order request-build admission and admission waits to `async_prefill=True`; retain main’s FIFO loop for Fun-ASR, ArkASR and other opt-out users, including builds that finish while an earlier request is being admitted. Skip repeated waits while prefill admission is blocked.
- Keep the established upstream MRoPE position path; the unvalidated position-reconstruction shortcut has been removed.

**Changed defaults:** Qwen3-ASR on NVIDIA CUDA enables async prefill; the shared scheduler default remains false. Numeric request-build/coalescing defaults are unchanged.

## Paired comparison on current main

Final candidate `e98bcf05e6d27d877cfb134900900ca6fad5d76a` against frozen main `2d5de98cd92b17df7974ac2ef4192b4a99263845`: qualification is pending. The pre-review tables were measured on 2026-10-17/18 against main `8fff1e0e8c99a710afe876d1514209e1157c5502`; their actual heads and complete descriptions are archived in the evidence link. They are not new-head results.

Radix H100 80GB; full SeedTTS EN/ZH; c1/c16/c32/c64; non-streaming and streaming; seeds 42/43 in main(42) → PR(42) → PR(43) → main(43) order, with matched settings and separate quality/failure reporting. No current-head gain is claimed until complete blocks are verified.

### Non-streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | Pending |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

### Streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | Pending |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

The preliminary c1 non-streaming block on superseded review head `207b2d0b` is archived separately. A later opt-out FIFO interleaving fix changed the final candidate; those measurements are not current-head results.

Detailed req/s, mean/p95 response and first-text latency, corpus WER, SIM (N/A for text-only ASR) and failed/attempted requests will be added after the paired blocks finish.

## Costs

Final-source startup-to-ready time, sampled peak GPU memory and live capture count deltas are pending. Historical costs retain their original source identities in the archive.

## Tests

- Review-fix source: **124 CUDA-hidden Qwen cases, 3 accelerator cases, and 250 CUDA-hidden scheduler / async-decode / Fun-ASR / ArkASR cases (8 skipped) passed** on the assigned H100; logs and source identities are in the evidence link.
- `pre-commit run --all-files`: passed. Complete diff versus the frozen main contains no `doc/` or `docs/` changes.
- Existing CI labels: `run-asr-ci` + `run-asr-qwen3-asr-1.7b`. [Current-head Omni CI](https://github.com/sgl-project/sglang-omni/actions/runs/39288752772) (attempt 1): preflight passed and verified `run_asr=true`, `asr_ci_model=qwen3` for `e98bcf05`; unit, accelerator and ASR completion remains pending. Earlier runs are historical evidence.
- Added a deterministic regression in which a second build finishes during the first admission; main and this head collect both in the same call. The prior review head did not.
- Review-specific validation pending: async-prefill/admission ablation, fixed-seed42 repeats and normalized transcript inspection, separately labeled from standalone main comparisons.
- Performance readiness remains pending until final-source comparisons, costs and current CI are verified.

Developed by an autonomous research agent using [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) in [OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index), with co-author [Kangda Wei (@WeiKangda)](https://github.com/WeiKangda); [qualification and historical evidence](https://github.com/Zhuofeng-Li/sglang-omni/tree/codex/omni-review-evidence-20261019/pr-2881).
