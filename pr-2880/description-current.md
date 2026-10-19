## Changes

**Merged:** db-ol merged the reviewed head `67e28de8` as `cba9d418ad242077831982a32f3c55e3509a8826` on 2026-10-19T22:17:05Z. The standalone final-head measurements still running below are post-merge qualification on the frozen control; they do not represent the combined merged series. Final series validation remains required after the remaining Qwen PR #2881 lands.

- Preserve the full LM prefill limit when a CUDA graph override only changes decode; explicit prefill values still win.
- Distinguish omitted decode buckets from operator-supplied buckets, including a sparse list equal to the shared default ladder.
- Capture decode metadata with thread-local CUDA capture and test concurrent CUDA submission, capture and replay outputs.

**Changed defaults:** CUDA prefill backend `full` with a 32-request cap; default decode buckets are exact sizes; Qwen stage metadata glue graphs default on. Explicit operator overrides remain authoritative.

## Paired comparison on current main

Measured **2026-10-19 UTC**. **3 of eight final-head primary ABBA blocks are verified:** c1 nonstream, c1 stream, c16 nonstream. Unverified cells remain Pending. Observed upstream main is `a2a3861fe4319eaedbfa47554d71c519a01c2e23`; the paired baseline stays frozen at `2d5de98cd92b17df7974ac2ef4192b4a99263845`. These independent frozen-head comparisons do not measure the combined merged series.

Model `Qwen/Qwen3-ASR-1.7B@7278e1e70fe206f11671096ffdd38061171dd6e5`, BF16; dataset `zhaochenyang20/seed-tts-eval-arrow@27f4c1adee83b5b29b7c4b375f6b976324bda308`. Original Radix H100 80GB (`GPU-e9f60c1d-8856-043c-42cd-47a942a4d8f1`), Torch 2.13.0+cu130, SGLang 0.5.21, Transformers 5.12.1. Every fresh service fully warms and scores both splits. YAML uses `Qwen3ASRPipelineConfig`, ASR GPU0, BF16, `pre_lm_cache_size_bytes=1`, `mm_embedding_cache_size_bytes=0`, `disable_radix_cache=true`, and `random_seed=42|43`; greedy decoding, no client token override, isolated fresh compilation caches. Exact YAML, source/asset identities and costs are under `primary-matrix/` at the evidence link.

Historical complete matrices retain their original dates, main and candidate identities in `description-before-final-head-backfill.md`. The intervening Qwen API startup GC default change (#2609) and evidence reuse assessment are recorded in `performance-evidence-applicability-20261019.json`.

Candidate `67e28de826af967a9dec76506c91473e257aa156` vs frozen main `2d5de98cd92b17df7974ac2ef4192b4a99263845`.

H100 80GB, SeedTTS EN (1088) / ZH (2020), seeds 42/43; each block runs main(42) → PR(42) → PR(43) → main(43). Throughput and mean latency are arithmetic means across the two seeds. P95, first-text latency and corpus WER retain seed42/43 values. Geometric change uses the ratio of mean req/s for each language, followed by the geometric mean of the two language ratios. Missing or incompletely paired blocks remain Pending. ASR SIM is N/A because the output is text.

### Non-streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | +1.34% |
| 16 | +0.32% |
| 32 | Pending |
| 64 | Pending |

Detailed metrics (main → PR; slash-separated values retain seed42/43):

| c / split | req/s | Mean response ms | P95 response ms | First-text mean ms | First-text P95 ms | WER % | Failed/attempted |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| 1 / EN | 24.520 → 24.935 | 40.63 → 39.97 | 49.63/49.89 → 48.69/49.06 | N/A → N/A | N/A → N/A | 1.2258/1.2258 → 1.2258/1.2258 | 0/2176 → 0/2176 |
| 1 / ZH | 26.896 → 27.164 | 37.01 → 36.67 | 47.04/47.01 → 46.46/47.00 | N/A → N/A | N/A → N/A | 0.5933/0.5933 → 0.5933/0.5933 | 0/4040 → 0/4040 |
| 16 / EN | 148.344 → 149.407 | 107.14 → 106.27 | 140.49/140.10 → 138.74/143.46 | N/A → N/A | N/A → N/A | 1.2031/1.2031 → 1.2031/1.2031 | 0/2176 → 0/2176 |
| 16 / ZH | 155.129 → 155.002 | 101.87 → 101.94 | 138.20/137.57 → 136.92/138.22 | N/A → N/A | N/A → N/A | 0.5933/0.5874 → 0.5844/0.6023 | 0/4040 → 0/4040 |

### Streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | +2.07% |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

Detailed metrics (main → PR; slash-separated values retain seed42/43):

| c / split | req/s | Mean response ms | P95 response ms | First-text mean ms | First-text P95 ms | WER % | Failed/attempted |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| 1 / EN | 24.375 → 24.876 | 40.87 → 40.07 | 50.10/49.72 → 49.14/49.29 | 12.40/12.20 → 11.70/11.70 | 14.10/14.00 → 13.10/13.50 | 1.2258/1.2258 → 1.2258/1.2258 | 0/2176 → 0/2176 |
| 1 / ZH | 26.745 → 27.300 | 37.21 → 36.48 | 47.28/47.36 → 46.81/46.07 | 12.10/11.90 → 11.70/11.40 | 13.40/13.50 → 12.70/12.50 | 0.5933/0.5933 → 0.5933/0.5933 | 0/4040 → 0/4040 |

Per-seed quality and latency changes are retained in the detailed tables. No outliers are removed. The completed subset does not establish output equivalence or completion of the remaining matrix/transcript checks.

**Observed tradeoffs in completed blocks:** C16 non-streaming throughput change is close to zero (+0.32%). ZH corpus WER improves at seed42 (0.5933→0.5844%) and worsens at seed43 (0.5874→0.6023%); EN response p95 at seed43 increases140.10→143.46ms, and ZH137.57→138.22ms. Mean startup increases about0.48s; maximum sampled memory is71.45→71.74GiB. These seed-level regressions and costs are retained, without claiming stable benefit or output equivalence.

## Costs

Startup is server launch to health-ready, including model/graph initialization and excluding downloads/workload warmup. Device memory is sampled every0.5s. Only verified blocks are tabulated; other costs remain Pending.

Per-cohort startup-to-ready, sampled peak device memory and successful CUDA capture calls (seed42/43; main → PR). Capture calls include segmented prefill captures; they are not unique shape counts. No pooled quantiles or inferred unmeasured costs.

| Mode / c | Startup s | Peak GiB | Successful captures | Live captures after scoring | Capture delta |
| --- | --- | --- | --- | --- | --- |
| nonstream / 1 | 76.75/75.58 → 77.18/77.60 | 70.80/70.79 → 70.78/70.77 | 1468/1468 → 121/121 | 1468/1468 → 121/121 | -1347/-1347 |
| nonstream / 16 | 76.33/77.07 → 77.28/77.08 | 71.45/71.42 → 71.45/71.74 | 1468/1468 → 136/136 | 1468/1468 → 136/136 | -1332/-1332 |
| stream / 1 | 76.11/76.13 → 77.10/78.10 | 70.80/70.79 → 70.78/70.77 | 1468/1468 → 121/121 | 1468/1468 → 121/121 | -1347/-1347 |

## Tests

- Final-head primary backfill: **3/8 blocks verified**, 24/64 language/cohort cells: c1 nonstream, c1 stream, c16 nonstream. Remaining primary blocks, full-split review ablations/repeats and transcript comparisons continue in the existing queue. This PR has already merged; post-merge qualification is continuing. Full merged-series validation and tradeoff assessment remain required.
- **Reviewer approval obtained for current head** `67e28de8`: db-ol approved on 2026-10-19T22:17:01Z, noting the explicit-override/fallback scope and passed CI. The post-merge final-source comparison on the changed baseline remains incomplete; the old measured source/base is kept explicit above.
- Review-fix source: **137 CPU tests and 5 accelerator tests passed** on the assigned H100; logs and source identities are in the evidence link.
- Final review-fix head `67e28de8` **FlashInfer smoke passed in both modes** on the original Radix H100 (2026-10-19): c32, seed42, eager frozen-main reference versus FULL candidate, metadata glue disabled in all four services, EN8/ZH8 each (**64 scored requests, 0 failures**). Each FULL cohort recorded **50 successful prefill capture stacks containing both the prefill runner and FULL backend**, with FlashInfer startup-log evidence. This is small-sample backend-path coverage, not a throughput or quality claim; the full EN/ZH two-seed backend comparison and final-head primary matrix remain pending. Audit, YAML, costs and capture evidence are under `flashinfer-smoke-20261019/` at the evidence link below.
- `pre-commit run --all-files`: passed. Complete diff versus the frozen main contains no `doc/` or `docs/` changes.
- Current-head [Omni CI](https://github.com/sgl-project/sglang-omni/actions/runs/39282362618) passed (attempt 2). Existing labels: `run-asr-ci` + `run-asr-qwen3-asr-1.7b`; preflight selected `run_asr=true`, `asr_ci_model=qwen3`, and stage-2 logs confirm **Qwen/Qwen3-ASR-1.7B**. Unit, accelerator, MOSS-TD prerequisite and Qwen SeedTTS stages passed; unselected stages are not hardware-validation evidence.
- Current-head ordinary CI: **9032 passed, 86 skipped**; accelerator CI: **771 passed, 15 skipped**. Tested synthetic merge revisions and logs are archived in the evidence.
- CPU/XPU workflow gate retries passed after the initial lint-wait cancellations. Intel CPU/XPU tests were skipped by the unchanged stage selection; this is gate recovery, not Intel hardware validation.

Developed by an autonomous research agent using [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) in [OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index), with co-author [Kangda Wei (@WeiKangda)](https://github.com/WeiKangda); [qualification and historical evidence](https://github.com/Zhuofeng-Li/sglang-omni/tree/codex/omni-review-evidence-20261019/pr-2880).

