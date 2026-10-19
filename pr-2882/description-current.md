## Changes

- Plan mel chunking and encoder layout on the host, then execute the planned preamble with the encoder graph.
- Reject uncovered/failed graph buckets before either planned or eager convolution work; the full-tower fallback runs its frontend once.
- Cover successful planned routing, runner rejection, fallback routing and BF16 accelerator parity with the eager preamble.

**Changed defaults:** no numeric configuration default changes.

## Paired comparison on current main

Final candidate `2cad178053585b41d486c1584796d58b205541a0` against frozen main `2d5de98cd92b17df7974ac2ef4192b4a99263845`: qualification is pending. The pre-review tables were measured on 2026-10-17/18 against main `8fff1e0e8c99a710afe876d1514209e1157c5502`; their actual heads and complete descriptions are archived in the evidence link. They are not new-head results.

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

- Review-fix source: **136 CPU tests and 3 accelerator tests passed** on the assigned H100; logs and source identities are in the evidence link.
- `pre-commit run --all-files`: passed. Complete diff versus the frozen main contains no `doc/` or `docs/` changes.
- Current-head [Omni CI](https://github.com/sgl-project/sglang-omni/actions/runs/39282431325) passed (attempt 2). Existing labels: `run-asr-ci` + `run-asr-qwen3-asr-1.7b`; preflight selected `run_asr=true`, `asr_ci_model=qwen3`, and stage-2 logs confirm **Qwen/Qwen3-ASR-1.7B**. Unit, accelerator, MOSS-TD prerequisite and Qwen SeedTTS stages passed; unselected stages are not hardware-validation evidence.
- Current-head ordinary CI: **9031 passed, 86 skipped**; accelerator CI: **769 passed, 15 skipped**. Tested synthetic merge revisions and logs are archived in the evidence.
- CPU/XPU workflow gate retries passed after the initial lint-wait cancellations. Intel CPU/XPU tests were skipped by the unchanged stage selection; this is gate recovery, not Intel hardware validation.
- Performance readiness remains pending until final-source primary comparisons and requested additional review validations are complete; current CI has passed.

Developed by an autonomous research agent using [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) in [OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index), with co-author [Kangda Wei (@WeiKangda)](https://github.com/WeiKangda); [qualification and historical evidence](https://github.com/Zhuofeng-Li/sglang-omni/tree/codex/omni-review-evidence-20261019/pr-2882).
