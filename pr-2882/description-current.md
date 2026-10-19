## Changes

**Merged:** db-ol merged the reviewed head `2cad1780` as `a2a3861fe4319eaedbfa47554d71c519a01c2e23` on 2026-10-19T22:21:56Z. The standalone final-head measurements still running below are post-merge qualification on the frozen control; they do not represent the combined merged series. Final series validation remains required after the remaining Qwen PR #2881 lands.

- Plan mel chunking and encoder layout on the host, then execute the planned preamble with the encoder graph.
- Reject uncovered/failed graph buckets before either planned or eager convolution work; the full-tower fallback runs its frontend once.
- Cover successful planned routing, runner rejection, fallback routing and BF16 accelerator parity with the eager preamble.

**Changed defaults:** no numeric configuration default changes.

## Paired comparison on current main

Measured **2026-10-19 UTC**. **1 of eight final-head primary ABBA blocks are verified:** c1 nonstream. Unverified cells remain Pending. Observed upstream main is `1240a6993c8073593aa0ad074859ccee2797adff`; the paired baseline stays frozen at `2d5de98cd92b17df7974ac2ef4192b4a99263845`. These independent frozen-head comparisons do not measure the combined merged series.

Model `Qwen/Qwen3-ASR-1.7B@7278e1e70fe206f11671096ffdd38061171dd6e5`, BF16; dataset `zhaochenyang20/seed-tts-eval-arrow@27f4c1adee83b5b29b7c4b375f6b976324bda308`. Original Radix H100 80GB (`GPU-e9f60c1d-8856-043c-42cd-47a942a4d8f1`), Torch 2.13.0+cu130, SGLang 0.5.21, Transformers 5.12.1. Every fresh service fully warms and scores both splits. YAML uses `Qwen3ASRPipelineConfig`, ASR GPU0, BF16, `pre_lm_cache_size_bytes=1`, `mm_embedding_cache_size_bytes=0`, `disable_radix_cache=true`, and `random_seed=42|43`; greedy decoding, no client token override, fresh per-cohort Inductor, Triton, CUDA, Torch extensions and FlashInfer workspace directories; the package/image and default SGLang JIT cache are retained across cohorts (see `cache-protocol.json`). Exact YAML, source/asset identities and costs are under `primary-matrix/` at the evidence link.

Historical complete matrices retain their original dates, main and candidate identities in `description-before-final-head-backfill.md`. The intervening Qwen API startup GC default change (#2609) and evidence reuse assessment are recorded in `performance-evidence-applicability-20261019.json`.

Candidate `2cad178053585b41d486c1584796d58b205541a0` vs frozen main `2d5de98cd92b17df7974ac2ef4192b4a99263845`.

H100 80GB, SeedTTS EN (1088) / ZH (2020), seeds 42/43; each block runs main(42) → PR(42) → PR(43) → main(43). Throughput and mean latency are arithmetic means across the two seeds. P95, first-text latency and corpus WER retain seed42/43 values. Geometric change uses the ratio of mean req/s for each language, followed by the geometric mean of the two language ratios. Missing or incompletely paired blocks remain Pending. ASR SIM is N/A because the output is text.

### Non-streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | +1.37% |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

Detailed metrics (main → PR; slash-separated values retain seed42/43):

| c / split | req/s | Mean response ms | P95 response ms | First-text mean ms | First-text P95 ms | WER % | Failed/attempted |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| 1 / EN | 24.584 → 24.854 | 40.53 → 40.09 | 49.24/49.61 → 49.34/48.79 | N/A → N/A | N/A → N/A | 1.2258/1.2258 → 1.2258/1.2258 | 0/2176 → 0/2176 |
| 1 / ZH | 27.266 → 27.712 | 36.53 → 35.95 | 46.11/46.72 → 46.27/45.24 | N/A → N/A | N/A → N/A | 0.5933/0.5933 → 0.5933/0.5933 | 0/4040 → 0/4040 |

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

Per-seed quality and latency changes are retained in the detailed tables. No outliers are removed. The completed subset does not establish output equivalence or completion of the remaining matrix/transcript checks.

**Observed tradeoffs in completed blocks:** C1 non-streaming geometric throughput change is +1.37%. Corpus WER is identical at both seeds/languages, with zero failures. Seed42 response p95 increases slightly: EN 49.24→49.34 ms and ZH 46.11→46.27 ms; both seed43 p95 values improve. Mean startup decreases about 0.42 s and maximum sampled device memory is 70.80→70.79 GiB; successful/live capture events remain 1468 per service. This single completed block does not establish a stable benefit across the remaining workloads or output equivalence.

## Costs

Startup is server launch to health-ready, including model/graph initialization and excluding downloads/workload warmup. These are starts under the disclosed partial cache isolation, not universally cold JIT starts. Device memory is sampled every0.5s. Only verified blocks are tabulated; other costs remain Pending.

Per-cohort startup-to-ready, sampled peak device memory and successful CUDA capture calls (seed42/43; main → PR). Capture calls include segmented prefill captures; they are not unique shape counts. No pooled quantiles or inferred unmeasured costs.

| Mode / c | Startup s | Peak GiB | Successful captures | Live captures after scoring | Capture delta |
| --- | --- | --- | --- | --- | --- |
| nonstream / 1 | 75.72/75.77 → 74.58/76.08 | 70.80/70.79 → 70.79/70.79 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |

## Tests

- Final-head primary backfill: **1/8 blocks verified**, 8/64 language/cohort cells: c1 nonstream. Review-specific ablations/repeats and transcript checks are tracked separately from primary coverage. This PR has already merged; post-merge qualification is continuing. These independent comparisons do not replace final merged-series validation or tradeoff assessment.
- **Reviewer approval obtained for current head** `2cad1780`: db-ol approved on 2026-10-19T22:21:47Z, noting the explicit-override/fallback scope and passed CI. The post-merge final-source comparison on the changed baseline remains pending; historical measurements retain their actual source/base in the linked archive.
- Review-fix source: **136 CPU tests and 3 accelerator tests passed** on the assigned H100; logs and source identities are in the evidence link.
- `pre-commit run --all-files`: passed. Complete diff versus the frozen main contains no `doc/` or `docs/` changes.
- Current-head [Omni CI](https://github.com/sgl-project/sglang-omni/actions/runs/39282431325) passed (attempt 2). Existing labels: `run-asr-ci` + `run-asr-qwen3-asr-1.7b`; preflight selected `run_asr=true`, `asr_ci_model=qwen3`, and stage-2 logs confirm **Qwen/Qwen3-ASR-1.7B**. Unit, accelerator, MOSS-TD prerequisite and Qwen SeedTTS stages passed; unselected stages are not hardware-validation evidence.
- Current-head ordinary CI: **9031 passed, 86 skipped**; accelerator CI: **769 passed, 15 skipped**. Tested synthetic merge revisions and logs are archived in the evidence.
- CPU/XPU workflow gate retries passed after the initial lint-wait cancellations. Intel CPU/XPU tests were skipped by the unchanged stage selection; this is gate recovery, not Intel hardware validation.

Developed by an autonomous research agent using [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) in [OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index), with co-author [Kangda Wei (@WeiKangda)](https://github.com/WeiKangda); [qualification and historical evidence](https://github.com/Zhuofeng-Li/sglang-omni/tree/codex/omni-review-evidence-20261019/pr-2882).
