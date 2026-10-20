## Changes

**Merged:** db-ol merged the reviewed head `2cad1780` as `a2a3861fe4319eaedbfa47554d71c519a01c2e23` on 2026-10-19T22:21:56Z. The completed standalone final-head primary measurements below are post-merge qualification on the frozen control; they do not represent the combined merged series. Final series validation remains required after the remaining Qwen PR #2881 lands.

- Plan mel chunking and encoder layout on the host, then execute the planned preamble with the encoder graph.
- Reject uncovered/failed graph buckets before either planned or eager convolution work; the full-tower fallback runs its frontend once.
- Cover successful planned routing, runner rejection, fallback routing and BF16 accelerator parity with the eager preamble.

**Changed defaults:** no numeric configuration default changes.

## Paired comparison on current main

Measured **2026-10-19 through 2026-10-20 UTC**. **8 of eight final-head primary ABBA blocks are verified:** c1 nonstream, c1 stream, c16 nonstream, c16 stream, c32 nonstream, c32 stream, c64 nonstream, c64 stream. All primary cells are verified; review-specific and final merged-series checks are tracked separately. Observed upstream main is `1240a6993c8073593aa0ad074859ccee2797adff`; the paired baseline stays frozen at `2d5de98cd92b17df7974ac2ef4192b4a99263845`. These independent frozen-head comparisons do not measure the combined merged series.

Model `Qwen/Qwen3-ASR-1.7B@7278e1e70fe206f11671096ffdd38061171dd6e5`, BF16; dataset `zhaochenyang20/seed-tts-eval-arrow@27f4c1adee83b5b29b7c4b375f6b976324bda308`. Original Radix H100 80GB (`GPU-e9f60c1d-8856-043c-42cd-47a942a4d8f1`), Torch 2.13.0+cu130, SGLang 0.5.21, Transformers 5.12.1. Every fresh service fully warms and scores both splits. YAML uses `Qwen3ASRPipelineConfig`, ASR GPU0, BF16, `pre_lm_cache_size_bytes=1`, `mm_embedding_cache_size_bytes=0`, `disable_radix_cache=true`, and `random_seed=42|43`; greedy decoding, no client token override, fresh per-cohort Inductor, Triton, CUDA, Torch extensions and FlashInfer workspace directories; the package/image and default SGLang JIT cache are retained across cohorts (see `cache-protocol.json`). Exact YAML, source/asset identities and costs are under `primary-matrix/` at the evidence link.

Historical complete matrices retain their original dates, main and candidate identities in `description-before-final-head-backfill.md`. The intervening Qwen API startup GC default change (#2609) and evidence reuse assessment are recorded in `performance-evidence-applicability-20261019.json`.

Candidate `2cad178053585b41d486c1584796d58b205541a0` vs frozen main `2d5de98cd92b17df7974ac2ef4192b4a99263845`.

H100 80GB, SeedTTS EN (1088) / ZH (2020), seeds 42/43; each block runs main(42) → PR(42) → PR(43) → main(43). Throughput and mean latency are arithmetic means across the two seeds. P95, first-text latency and corpus WER retain seed42/43 values. Geometric change uses the ratio of mean req/s for each language, followed by the geometric mean of the two language ratios. Missing or incompletely paired blocks remain Pending. ASR SIM is N/A because the output is text.

### Non-streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | +1.37% |
| 16 | -0.52% |
| 32 | -0.81% |
| 64 | -0.23% |

Detailed metrics (main → PR; slash-separated values retain seed42/43):

| c / split | req/s | Mean response ms | P95 response ms | First-text mean ms | First-text P95 ms | WER % | Failed/attempted |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| 1 / EN | 24.584 → 24.854 | 40.53 → 40.09 | 49.24/49.61 → 49.34/48.79 | N/A → N/A | N/A → N/A | 1.2258/1.2258 → 1.2258/1.2258 | 0/2176 → 0/2176 |
| 1 / ZH | 27.266 → 27.712 | 36.53 → 35.95 | 46.11/46.72 → 46.27/45.24 | N/A → N/A | N/A → N/A | 0.5933/0.5933 → 0.5933/0.5933 | 0/4040 → 0/4040 |
| 16 / EN | 149.267 → 147.654 | 106.39 → 107.65 | 138.76/140.55 → 141.96/142.46 | N/A → N/A | N/A → N/A | 1.2031/1.2107 → 1.2031/1.2031 | 0/2176 → 0/2176 |
| 16 / ZH | 155.648 → 155.718 | 102.20 → 102.07 | 138.03/138.85 → 138.65/138.32 | N/A → N/A | N/A → N/A | 0.5904/0.6023 → 0.5993/0.5993 | 0/4040 → 0/4040 |
| 32 / EN | 226.762 → 225.034 | 139.04 → 140.05 | 181.47/178.47 → 180.73/192.88 | N/A → N/A | N/A → N/A | 1.2031/1.2031 → 1.2107/1.2107 | 0/2176 → 0/2176 |
| 32 / ZH | 244.047 → 241.955 | 130.22 → 131.44 | 169.75/171.92 → 174.00/175.26 | N/A → N/A | N/A → N/A | 0.6023/0.6143 → 0.6083/0.6113 | 0/4040 → 0/4040 |
| 64 / EN | 289.709 → 289.472 | 217.68 → 214.78 | 285.25/342.31 → 346.97/289.45 | N/A → N/A | N/A → N/A | 1.2182/1.2031 → 1.2107/1.2031 | 0/2176 → 0/2176 |
| 64 / ZH | 304.926 → 303.769 | 206.65 → 203.54 | 284.96/277.41 → 279.06/271.02 | N/A → N/A | N/A → N/A | 0.6203/0.6203 → 0.6203/0.6173 | 0/4040 → 0/4040 |

### Streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | +1.53% |
| 16 | +1.16% |
| 32 | +0.57% |
| 64 | +4.50% |

Detailed metrics (main → PR; slash-separated values retain seed42/43):

| c / split | req/s | Mean response ms | P95 response ms | First-text mean ms | First-text P95 ms | WER % | Failed/attempted |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| 1 / EN | 24.744 → 24.844 | 40.26 → 40.10 | 49.29/49.40 → 49.27/49.55 | 11.70/12.00 → 11.50/11.40 | 12.80/13.60 → 13.20/13.20 | 1.2258/1.2258 → 1.2258/1.2258 | 0/2176 → 0/2176 |
| 1 / ZH | 26.947 → 27.668 | 36.96 → 36.00 | 47.14/46.81 → 45.17/46.62 | 11.80/11.90 → 11.00/11.30 | 13.00/13.20 → 11.80/12.60 | 0.5933/0.5933 → 0.5933/0.5933 | 0/4040 → 0/4040 |
| 16 / EN | 146.619 → 148.205 | 108.17 → 107.01 | 143.72/141.54 → 139.48/143.98 | 58.00/58.00 → 55.60/56.60 | 80.40/81.80 → 77.50/80.60 | 1.2031/1.2031 → 1.2031/1.2031 | 0/2176 → 0/2176 |
| 16 / ZH | 153.651 → 155.558 | 103.46 → 102.25 | 139.11/139.43 → 138.80/138.75 | 58.90/59.60 → 57.50/56.60 | 79.40/80.00 → 78.40/79.70 | 0.5874/0.6053 → 0.5963/0.5993 | 0/4040 → 0/4040 |
| 32 / EN | 221.968 → 224.109 | 142.46 → 140.89 | 188.99/183.08 → 189.16/184.60 | 70.70/70.90 → 68.30/69.20 | 99.50/100.80 → 97.10/102.40 | 1.2182/1.2107 → 1.2031/1.2031 | 0/2176 → 0/2176 |
| 32 / ZH | 236.641 → 237.070 | 132.58 → 134.04 | 174.43/175.25 → 178.63/177.42 | 66.50/67.80 → 65.40/68.20 | 95.10/96.80 → 94.40/98.90 | 0.6053/0.6113 → 0.6083/0.6083 | 0/4040 → 0/4040 |
| 64 / EN | 275.858 → 284.012 | 226.60 → 219.75 | 359.47/283.76 → 330.27/296.02 | 102.30/92.90 → 96.00/91.40 | 267.00/178.60 → 271.30/174.90 | 1.2107/1.2182 → 1.2182/1.2031 | 0/2176 → 0/2176 |
| 64 / ZH | 287.753 → 305.223 | 217.74 → 207.62 | 289.64/295.85 → 275.54/284.30 | 95.30/98.70 → 90.80/90.30 | 136.40/136.30 → 134.80/126.80 | 0.6233/0.6233 → 0.6083/0.6023 | 0/4040 → 0/4040 |

Per-seed quality and latency changes are retained in the detailed tables. No outliers are removed. The complete primary matrix does not establish output equivalence or completion of the separately tracked review-specific and final merged-series checks.

**Observed tradeoffs in completed blocks:** C1 non-streaming geometric throughput change is +1.37%. Corpus WER is identical at both seeds/languages, with zero failures. Seed42 response p95 increases slightly: EN 49.24→49.34 ms and ZH 46.11→46.27 ms; both seed43 p95 values improve. Mean startup decreases about 0.42 s and maximum sampled device memory is 70.80→70.79 GiB; successful/live capture events remain 1468 per service. This single completed block does not establish a stable benefit across the remaining workloads or output equivalence.

C1 non-streaming transcript inspection: all 6,216 paired normalized hypotheses agree across both seeds/languages. This finite-sample agreement is specific to the completed block; other primary blocks and review repeats are evaluated separately. The checked comparisons are archived in `primary-matrix/quality-c1-nonstream.json`.

C1 streaming geometric throughput change is +1.53%, with identical corpus WER at both seeds/languages and zero failures. EN first-text p95 at seed42 increases 12.80→13.20 ms, while seed43 improves 13.60→13.20 ms; EN response p95 at seed43 rises 49.40→49.55 ms. ZH response and first-text p95 improve at both seeds. Mean startup decreases about 0.26 s, maximum sampled device memory is 70.80→70.79 GiB, and capture events remain 1468 per service. This small measured gain does not establish a stable benefit across workloads.

C1 streaming transcript inspection found one changed normalized hypothesis among 6,216 pairs: at EN seed43, reference `serer` is transcribed as `sireer` on main and `siree` on PR, with equal per-sample WER. All other paired hypotheses agree in this block. This equal-WER text difference is retained in `primary-matrix/quality-c1-stream.json`; output equivalence is not claimed.

C16 non-streaming geometric throughput change is **−0.52%**: EN 149.267→147.654 req/s, ZH 155.648→155.718. EN response p95 worsens at both seeds, 138.76/140.55→141.96/142.46 ms; ZH seed42 also worsens 138.03→138.65 ms (seed43 improves). ZH corpus WER worsens at seed42, 0.5904→0.5993%, and improves at seed43, 0.6023→0.5993%; EN seed43 improves and seed42 is unchanged. Mean startup increases about **4.52 s**; maximum sampled memory is 71.60→71.42 GiB, captures remain 1468, and all requests succeed. This negative throughput point and its latency/quality/startup costs are retained.

C16 non-streaming transcript inspection covers all 6,216 pairs: 9 changed hypotheses, with 3 WER improvements, 3 regressions and 3 equal-WER changes; all 8 distinct reference/main/PR triples were inspected. Differences involve proper names, homophones and an erhua insertion; there are no empty hypotheses. Full changed text is archived in `primary-matrix/quality-c16-nonstream.json`. These observations do not establish a numerical cause or output equivalence.

C16 streaming geometric throughput change is +1.16%. First-text p95 improves at both seeds/languages: EN 80.40/81.80→77.50/80.60 ms, ZH 79.40/80.00→78.40/79.70 ms. EN response p95 at seed43 worsens 141.54→143.98 ms. ZH corpus WER worsens at seed42, 0.5874→0.5963%, and improves at seed43, 0.6053→0.5993%; both EN values are unchanged. Mean startup increases about 0.14 s; maximum sampled memory is 71.75→71.62 GiB, capture events remain 1468, and all requests succeed. This modest gain coexists with the retained latency/quality tradeoffs and the negative non-streaming c16 point.

C16 streaming transcript inspection covers 6,216 pairs: 9 changed hypotheses, with 3 WER improvements, 3 regressions and 3 equal-WER changes; all 7 distinct triples were inspected. The changes involve a name-spelling variant, Chinese names/homophones and an erhua deletion; no hypothesis is empty. Full changed text is archived in `primary-matrix/quality-c16-stream.json`; output equivalence and a numerical cause are not claimed.

C32 non-streaming geometric throughput change is **−0.81%**, with lower mean req/s in both languages. EN response p95 at seed43 worsens 178.47→192.88 ms; ZH p95 worsens at both seeds, 169.75/171.92→174.00/175.26 ms. EN corpus WER worsens at both seeds, 1.2031/1.2031→1.2107/1.2107%; ZH worsens at seed42, 0.6023→0.6083%, and improves at seed43, 0.6143→0.6113%. Mean startup decreases about 0.25 s, maximum sampled memory is 71.61→71.60 GiB, captures remain 1468 and all requests succeed. The negative throughput and quality/tail outcomes are retained; the predefined fixed-seed c32 repeats remain separate pending checks.

C32 non-streaming transcript inspection covers 6,216 pairs: 15 changed hypotheses, with 5 WER improvements, 8 regressions and 2 equal-WER changes; all 11 distinct triples were inspected. Changes include an English plural loss, proper names, Chinese homophones and erhua changes; no hypothesis is empty. Full changed text is archived in `primary-matrix/quality-c32-nonstream.json`; output equivalence and a numerical cause are not claimed.

C32 streaming geometric throughput change is **+0.57%**, close to zero. Response p95 worsens at all four seed/language points: EN 188.99/183.08→189.16/184.60 ms, ZH 174.43/175.25→178.63/177.42 ms. First-text p95 improves at seed42 but worsens at seed43: EN 100.80→102.40 ms and ZH 96.80→98.90 ms. EN corpus WER improves at both seeds, 1.2182/1.2107→1.2031/1.2031%; ZH worsens at seed42, 0.6053→0.6083%, and improves at seed43, 0.6113→0.6083%. Mean startup decreases about 2.74 s (the main seed43 startup of 83.14 s is retained); maximum sampled memory is 71.78→71.46 GiB, captures remain 1468 and all requests succeed. A stable throughput benefit is not established; predefined fixed-seed repeats remain pending.

C32 streaming transcript inspection covers 6,216 pairs: 20 changed hypotheses, with 10 WER improvements, 6 regressions and 4 equal-WER changes; all 16 distinct triples were inspected. Changes involve an English plural, proper names, Chinese homophones and erhua; no hypothesis is empty. Full changed text is archived in `primary-matrix/quality-c32-stream.json`; output equivalence and a numerical cause are not claimed.

C64 non-streaming geometric throughput change is **−0.23%**, effectively flat with slightly lower mean req/s in both languages. EN response p95 worsens at seed42, 285.25→346.97 ms, but improves at seed43, 342.31→289.45 ms; both outcomes are retained. ZH response p95 improves at both seeds. Corpus WER improves or stays equal at all four language/seed points, but individual transcript regressions remain below. Mean startup differs by less than 0.02 s; maximum sampled memory is 71.80→71.82 GiB, captures remain 1468 and all requests succeed. These results do not establish a stable throughput gain.

C64 non-streaming transcript inspection covers 6,216 pairs: 13 changed hypotheses, with 5 WER improvements, 4 regressions and 4 equal-WER changes; all 12 distinct triples were inspected. The changes involve English proper names/tern/turn and Chinese names/homophones, with some opposite directions across samples or seeds; no hypothesis is empty. Full changed text is archived in `primary-matrix/quality-c64-nonstream.json`; output equivalence and a numerical cause are not claimed.

C64 streaming geometric throughput change is **+4.50%**, the strongest measured primary point. EN response p95 worsens at seed43, 283.76→296.02 ms (seed42 improves); EN first-text p95 worsens at seed42, 267.00→271.30 ms (seed43 improves). ZH response/first-text p95 and WER improve at both seeds. EN corpus WER worsens at seed42, 1.2107→1.2182%, and improves at seed43, 1.2182→1.2031%. Mean startup decreases about 1.30 s; maximum sampled memory is 72.00→72.16 GiB, captures remain 1468 and all requests succeed. This positive streaming point does not remove the flat/negative non-streaming results or the retained quality/tail tradeoffs.

C64 streaming transcript inspection covers 6,216 pairs: 16 changed hypotheses, with 13 WER improvements, 1 regression and 2 equal-WER changes; all 13 distinct triples were inspected. Changes involve proper names, tern/turn, Chinese homophones and erhua deletions; no hypothesis is empty. Full changed text is archived in `primary-matrix/quality-c64-stream.json`.

**Complete primary transcript inspection:** 83 changed normalized hypotheses across 49,728 paired samples, with 39 WER improvements, 25 regressions and 19 equal-WER changes; all 30 distinct reference/main/PR triples were inspected. There are no empty changed hypotheses. These results do not establish output equivalence or a numerical cause. The complete primary changes and block inspection hashes are in `primary-matrix/quality-differences.json` and `quality-inspection-summary.json`; review-repeat comparisons remain pending.

## Costs

Startup is server launch to health-ready, including model/graph initialization and excluding downloads/workload warmup. These are starts under the disclosed partial cache isolation, not universally cold JIT starts. Device memory is sampled every0.5s. All primary-block costs are tabulated; review-specific costs are tracked separately.

Per-cohort startup-to-ready, sampled peak device memory and successful CUDA capture calls (seed42/43; main → PR). Capture calls include segmented prefill captures; they are not unique shape counts. No pooled quantiles or inferred unmeasured costs.

| Mode / c | Startup s | Peak GiB | Successful captures | Live captures after scoring | Capture delta |
| --- | --- | --- | --- | --- | --- |
| nonstream / 1 | 75.72/75.77 → 74.58/76.08 | 70.80/70.79 → 70.79/70.79 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
| nonstream / 16 | 77.09/78.59 → 82.11/82.60 | 71.60/71.58 → 71.27/71.42 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
| nonstream / 32 | 77.74/78.61 → 77.60/78.26 | 71.46/71.61 → 71.46/71.60 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
| nonstream / 64 | 77.60/77.13 → 77.10/77.60 | 71.80/71.66 → 71.81/71.82 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
| stream / 1 | 75.60/76.73 → 76.16/75.66 | 70.80/70.79 → 70.79/70.79 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
| stream / 16 | 79.11/77.33 → 78.61/78.11 | 71.43/71.75 → 71.62/71.42 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
| stream / 32 | 78.61/83.14 → 78.16/78.11 | 71.76/71.78 → 71.46/71.46 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
| stream / 64 | 79.11/80.17 → 81.11/75.58 | 72.00/72.00 → 72.16/71.80 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |

## Tests

- Final-head primary backfill: **8/8 blocks verified**, 64/64 language/cohort cells: c1 nonstream, c1 stream, c16 nonstream, c16 stream, c32 nonstream, c32 stream, c64 nonstream, c64 stream. Review-specific ablations/repeats and transcript checks are tracked separately from primary coverage. This PR has already merged; post-merge qualification is continuing. These independent comparisons do not replace final merged-series validation or tradeoff assessment.
- **Reviewer approval obtained for current head** `2cad1780`: db-ol approved on 2026-10-19T22:21:47Z, noting the explicit-override/fallback scope and passed CI. The post-merge final-source primary comparison is complete; review-specific and final merged-series qualification remain pending; historical measurements retain their actual source/base in the linked archive.
- Review-fix source: **136 CPU tests and 3 accelerator tests passed** on the assigned H100; logs and source identities are in the evidence link.
- `pre-commit run --all-files`: passed. Complete diff versus the frozen main contains no `doc/` or `docs/` changes.
- Current-head [Omni CI](https://github.com/sgl-project/sglang-omni/actions/runs/39282431325) passed (attempt 2). Existing labels: `run-asr-ci` + `run-asr-qwen3-asr-1.7b`; preflight selected `run_asr=true`, `asr_ci_model=qwen3`, and stage-2 logs confirm **Qwen/Qwen3-ASR-1.7B**. Unit, accelerator, MOSS-TD prerequisite and Qwen SeedTTS stages passed; unselected stages are not hardware-validation evidence.
- Current-head ordinary CI: **9031 passed, 86 skipped**; accelerator CI: **769 passed, 15 skipped**. Tested synthetic merge revisions and logs are archived in the evidence.
- CPU/XPU workflow gate retries passed after the initial lint-wait cancellations. Intel CPU/XPU tests were skipped by the unchanged stage selection; this is gate recovery, not Intel hardware validation.

Developed by an autonomous research agent using [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) in [OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index), with co-author [Kangda Wei (@WeiKangda)](https://github.com/WeiKangda); [qualification and historical evidence](https://github.com/Zhuofeng-Li/sglang-omni/tree/codex/omni-review-evidence-20261019/pr-2882).
