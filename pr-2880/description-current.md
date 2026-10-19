## Changes

- Preserve the full LM prefill limit when a CUDA graph override only changes decode; explicit prefill values still win.
- Distinguish omitted decode buckets from operator-supplied buckets, including a sparse list equal to the shared default ladder.
- Capture decode metadata with thread-local CUDA capture and test concurrent CUDA submission, capture and replay outputs.

**Changed defaults:** CUDA prefill backend `full` with a 32-request cap; default decode buckets are exact sizes; Qwen stage metadata glue graphs default on. Explicit operator overrides remain authoritative.

## Paired comparison on current main

Final candidate `67e28de826af967a9dec76506c91473e257aa156` against frozen main `2d5de98cd92b17df7974ac2ef4192b4a99263845`: qualification is pending. The pre-review tables were measured on 2026-10-17/18 against main `8fff1e0e8c99a710afe876d1514209e1157c5502`; their actual heads and complete descriptions are archived in the evidence link. They are not new-head results.

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

Detailed req/s, mean/p95 response and first-text latency, corpus WER, SIM (N/A for text-only ASR) and failed/attempted requests will be added after the paired blocks finish.

## Costs

Final-source startup-to-ready time, sampled peak GPU memory and live capture count deltas are pending. Historical costs retain their original source identities in the archive.

## Tests

- Review-fix source: **137 CPU tests and 5 accelerator tests passed** on the assigned H100; logs and source identities are in the evidence link.
- `pre-commit run --all-files`: passed. Complete diff versus the frozen main contains no `doc/` or `docs/` changes.
- Existing CI labels: `run-asr-ci` + `run-asr-qwen3-asr-1.7b`. [Current-head Omni CI](https://github.com/sgl-project/sglang-omni/actions/runs/39282362618) (attempt 2): preflight passed and verified `run_asr=true`, `asr_ci_model=qwen3` for `67e28de8`; unit, accelerator and ASR completion remains pending. Earlier runs are historical evidence.
- CPU/XPU workflow gate retries passed after the initial lint-wait cancellations. Intel CPU/XPU tests were skipped by the unchanged stage selection; this is gate recovery, not Intel hardware validation.
- Performance readiness remains pending until final-source comparisons, costs and current CI are verified.

Developed by an autonomous research agent using [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) in [OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index), with co-author [Kangda Wei (@WeiKangda)](https://github.com/WeiKangda); [qualification and historical evidence](https://github.com/Zhuofeng-Li/sglang-omni/tree/codex/omni-review-evidence-20261019/pr-2880).
