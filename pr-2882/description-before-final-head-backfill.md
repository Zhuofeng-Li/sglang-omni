Description snapshot before final-head tables. Historical paired tables retain their actual source/date; later Tests/merge status may be newer.

## Changes

**Merged:** db-ol merged the reviewed head `2cad1780` as `a2a3861fe4319eaedbfa47554d71c519a01c2e23` on 2026-10-19T22:21:56Z. The standalone final-head measurements still running below are post-merge qualification on the frozen control; they do not represent the combined merged series. Final series validation remains required after the remaining Qwen PR #2881 lands.

- Plan mel chunking and encoder layout on the host, then execute the planned preamble with the encoder graph.
- Reject uncovered/failed graph buckets before either planned or eager convolution work; the full-tower fallback runs its frontend once.
- Cover successful planned routing, runner rejection, fallback routing and BF16 accelerator parity with the eager preamble.

**Changed defaults:** no numeric configuration default changes.

## Paired comparison on current main

**Measurement scope:** The tables below retain the completed 2026-10-17/18 paired measurements at PR `0ab74d724a000ae2119dffc3dac3a028fea40c0a` versus main `8fff1e0e8c99a710afe876d1514209e1157c5502`. They are not measurements of review-fix head `2cad178053585b41d486c1584796d58b205541a0` against subsequently frozen main `2d5de98cd92b17df7974ac2ef4192b4a99263845`. Review-fix regression and CI results are listed under Tests. The reviewer approved this exact head and confirmed that the repairs affect explicit overrides/fallback paths. Historical pairs remain valid at their recorded revisions. However, between the old measured main and the new frozen baseline, Qwen3-ASR enabled API startup GC freeze (`3e90a4b5`, #2609), changing the default server path; shared FULL-prefill ladder handling also changed. The already-running final-head/current-baseline comparison addresses that actual baseline change, rather than repeating measurements because of their age. Source-diff and applicability details are archived as `performance-evidence-applicability-20261019.json` and `baseline-default-changes-8fff-to-2d.patch` at the evidence link. Existing measured results are retained unchanged.


Concurrency sweep at **C1, C16, C32 and C64**, with each PR evaluated independently. C32 was measured on 2026-10-17; C1/C16/C64 were measured on 2026-10-18. All tables use the same frozen measured main `8fff1e0e8c99a710afe876d1514209e1157c5502` and PR `0ab74d724a000ae2119dffc3dac3a028fea40c0a`. Latest upstream main observed at 2026-10-18T20:23:39.008260+00:00: `3a0655b84813b7d855d6bf042864b9ceaeb7a062`. The tables describe the frozen measured commit above.

- Single NVIDIA H100 80GB HBM3 per cohort. C1/C16/C64 use GPU `GPU-6a051904-54a1-9fbc-ed92-1c8ea133e232`; the reused C32 data uses `GPU-8c2e7fe8-6622-46fc-374a-1b0bea3c1a31`. Each main/PR pair runs on the same physical card. Cross-concurrency comparisons also include this card/date difference.
- Supplementary runs resolve both prefill and decode attention to **FA3**; representative main/PR startup logs were checked for all three PRs.
- CUDA 13.0 / Torch 2.13.0+cu130 / SGLang 0.5.21 / Transformers 5.12.1; model `Qwen/Qwen3-ASR-1.7B@7278e1e70fe206f11671096ffdd38061171dd6e5`, BF16. Dataset `zhaochenyang20/seed-tts-eval-arrow@27f4c1adee83b5b29b7c4b375f6b976324bda308`: complete EN (1,088) and ZH (2,020) splits.
- YAML: `results/pr2882-c<C>-<mode>-<arm>-seed<seed>/config.yaml`, using the frozen source's `Qwen3ASRPipelineConfig`. Overrides: model path `/qualification/assets/model`, ASR GPU 0; factory `dtype=bfloat16`, `pre_lm_cache_size_bytes=1`, `mm_embedding_cache_size_bytes=0`; engine `disable_radix_cache=true`, `random_seed=<seed>`. Greedy decoding and default duration-dependent output budget (128-token floor); no client token override. Full configurations and hashes are in the evidence link.
- For **each concurrency and mode**, seeds 42/43 use **main(42) → PR(42) → PR(43) → main(43)**. Seeds control sample shuffle, Python hash seed and engine RNG; paired sample-order hashes match. Every cohort starts a fresh service with empty compiler caches, then performs one full warmup and one scored pass per language. CPU uses the same default shared scheduling without quota/affinity changes.
- Each row below is an individual scored pass. Latencies are mean/p95 milliseconds per pass; percentiles are never pooled or averaged. Summary throughput is the geometric mean of EN/ZH PR/main ratios after averaging req/s across the two seeds within each language. Two seeds do not establish statistical significance. WER is corpus WER (ZH uses character tokens). SIM is N/A because ASR produces text. Streaming first text means the first nonempty delta; exact delta/final-text agreement and terminal DONE are checked.

### Non-streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | +0.43% |
| 16 | +0.53% |
| 32 | +1.81% |
| 64 | +0.25% |

| C / split / seed | Arm | req/s | Latency mean / p95 (ms) | First text mean / p95 (ms) | WER (%) | SIM | Failed / attempted |
| --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 / EN / 42 | Main | 24.88 | 40.07 / 48.83 | N/A: completed response | 1.2258 | N/A | 0 / 1088 |
| 1 / EN / 42 | PR | 24.82 | 40.16 / 49.13 | N/A: completed response | 1.2258 | N/A | 0 / 1088 |
| 1 / EN / 43 | Main | 24.96 | 39.93 / 48.77 | N/A: completed response | 1.2258 | N/A | 0 / 1088 |
| 1 / EN / 43 | PR | 24.96 | 39.84 / 48.86 | N/A: completed response | 1.2258 | N/A | 0 / 1088 |
| 1 / ZH / 42 | Main | 27.27 | 36.54 / 46.39 | N/A: completed response | 0.5933 | N/A | 0 / 2020 |
| 1 / ZH / 42 | PR | 27.83 | 35.80 / 45.45 | N/A: completed response | 0.5933 | N/A | 0 / 2020 |
| 1 / ZH / 43 | Main | 27.46 | 36.29 / 46.09 | N/A: completed response | 0.5933 | N/A | 0 / 2020 |
| 1 / ZH / 43 | PR | 27.45 | 36.31 / 46.37 | N/A: completed response | 0.5933 | N/A | 0 / 2020 |
| 16 / EN / 42 | Main | 146.25 | 108.59 / 143.29 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 16 / EN / 42 | PR | 147.65 | 107.31 / 142.54 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 16 / EN / 43 | Main | 150.07 | 105.96 / 138.37 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 16 / EN / 43 | PR | 150.26 | 105.62 / 139.90 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 16 / ZH / 42 | Main | 156.27 | 101.96 / 137.21 | N/A: completed response | 0.5874 | N/A | 0 / 2020 |
| 16 / ZH / 42 | PR | 156.93 | 101.53 / 136.27 | N/A: completed response | 0.5933 | N/A | 0 / 2020 |
| 16 / ZH / 43 | Main | 156.13 | 101.69 / 135.77 | N/A: completed response | 0.5993 | N/A | 0 / 2020 |
| 16 / ZH / 43 | PR | 157.09 | 101.21 / 138.32 | N/A: completed response | 0.5933 | N/A | 0 / 2020 |
| 32 / EN / 42 | Main | 220.02 | 139.71 / 179.80 | N/A: completed response | 1.2182 | N/A | 0 / 1088 |
| 32 / EN / 42 | PR | 228.47 | 138.13 / 184.42 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 32 / EN / 43 | Main | 224.57 | 140.26 / 188.40 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 32 / EN / 43 | PR | 230.14 | 137.42 / 180.96 | N/A: completed response | 1.2107 | N/A | 0 / 1088 |
| 32 / ZH / 42 | Main | 243.44 | 130.48 / 173.01 | N/A: completed response | 0.6113 | N/A | 0 / 2020 |
| 32 / ZH / 42 | PR | 243.80 | 129.95 / 174.10 | N/A: completed response | 0.6083 | N/A | 0 / 2020 |
| 32 / ZH / 43 | Main | 243.48 | 129.91 / 171.12 | N/A: completed response | 0.6053 | N/A | 0 / 2020 |
| 32 / ZH / 43 | PR | 245.51 | 129.35 / 171.33 | N/A: completed response | 0.6023 | N/A | 0 / 2020 |
| 64 / EN / 42 | Main | 278.07 | 225.90 / 309.76 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 64 / EN / 42 | PR | 286.64 | 220.47 / 301.20 | N/A: completed response | 1.2107 | N/A | 0 / 1088 |
| 64 / EN / 43 | Main | 291.76 | 214.87 / 294.02 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 64 / EN / 43 | PR | 293.11 | 215.09 / 289.80 | N/A: completed response | 1.2182 | N/A | 0 / 1088 |
| 64 / ZH / 42 | Main | 288.85 | 218.87 / 323.97 | N/A: completed response | 0.6203 | N/A | 0 / 2020 |
| 64 / ZH / 42 | PR | 286.11 | 221.61 / 363.67 | N/A: completed response | 0.6083 | N/A | 0 / 2020 |
| 64 / ZH / 43 | Main | 299.28 | 211.05 / 301.80 | N/A: completed response | 0.6293 | N/A | 0 / 2020 |
| 64 / ZH / 43 | PR | 294.87 | 212.87 / 310.89 | N/A: completed response | 0.6053 | N/A | 0 / 2020 |

Observed PR-minus-main ranges by concurrency (all four language/seed pairs):

- C1: p95 latency -0.94 to +0.30 ms; WER +0.0000 to +0.0000 percentage points.
- C16: p95 latency -0.94 to +2.55 ms; WER -0.0060 to +0.0060 percentage points.
- C32: p95 latency -7.44 to +4.62 ms; WER -0.0151 to +0.0076 percentage points.
- C64: p95 latency -8.56 to +39.70 ms; WER -0.0240 to +0.0151 percentage points.

### Streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | +2.76% |
| 16 | +0.40% |
| 32 | +0.74% |
| 64 | +3.29% |

| C / split / seed | Arm | req/s | Latency mean / p95 (ms) | First text mean / p95 (ms) | WER (%) | SIM | Failed / attempted |
| --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 / EN / 42 | Main | 24.51 | 40.66 / 49.87 | 11.90 / 13.30 | 1.2258 | N/A | 0 / 1088 |
| 1 / EN / 42 | PR | 25.10 | 39.71 / 48.69 | 11.40 / 12.80 | 1.2258 | N/A | 0 / 1088 |
| 1 / EN / 43 | Main | 24.95 | 39.95 / 48.93 | 11.80 / 13.20 | 1.2258 | N/A | 0 / 1088 |
| 1 / EN / 43 | PR | 24.89 | 40.04 / 49.14 | 11.30 / 12.50 | 1.2258 | N/A | 0 / 1088 |
| 1 / ZH / 42 | Main | 26.90 | 37.05 / 47.14 | 11.80 / 12.70 | 0.5933 | N/A | 0 / 2020 |
| 1 / ZH / 42 | PR | 28.21 | 35.32 / 44.97 | 11.10 / 12.00 | 0.5933 | N/A | 0 / 2020 |
| 1 / ZH / 43 | Main | 26.99 | 36.92 / 46.59 | 12.10 / 13.30 | 0.5933 | N/A | 0 / 2020 |
| 1 / ZH / 43 | PR | 28.08 | 35.47 / 45.08 | 10.90 / 11.80 | 0.5933 | N/A | 0 / 2020 |
| 16 / EN / 42 | Main | 147.30 | 107.64 / 143.13 | 57.70 / 80.10 | 1.2031 | N/A | 0 / 1088 |
| 16 / EN / 42 | PR | 148.50 | 107.05 / 141.83 | 56.40 / 77.30 | 1.2031 | N/A | 0 / 1088 |
| 16 / EN / 43 | Main | 148.45 | 106.72 / 141.11 | 58.60 / 82.30 | 1.2107 | N/A | 0 / 1088 |
| 16 / EN / 43 | PR | 147.99 | 107.33 / 142.50 | 56.40 / 80.60 | 1.2031 | N/A | 0 / 1088 |
| 16 / ZH / 42 | Main | 152.37 | 104.47 / 139.30 | 59.30 / 79.40 | 0.5963 | N/A | 0 / 2020 |
| 16 / ZH / 42 | PR | 153.62 | 103.64 / 140.77 | 57.10 / 78.60 | 0.5933 | N/A | 0 / 2020 |
| 16 / ZH / 43 | Main | 155.33 | 102.33 / 137.63 | 59.10 / 78.70 | 0.5993 | N/A | 0 / 2020 |
| 16 / ZH / 43 | PR | 155.76 | 102.04 / 137.86 | 57.40 / 79.80 | 0.6053 | N/A | 0 / 2020 |
| 32 / EN / 42 | Main | 222.60 | 141.63 / 181.48 | 70.90 / 101.00 | 1.2107 | N/A | 0 / 1088 |
| 32 / EN / 42 | PR | 223.54 | 141.38 / 194.63 | 68.10 / 107.30 | 1.2031 | N/A | 0 / 1088 |
| 32 / EN / 43 | Main | 220.28 | 143.25 / 183.64 | 72.90 / 100.90 | 1.2107 | N/A | 0 / 1088 |
| 32 / EN / 43 | PR | 226.41 | 139.59 / 178.02 | 67.70 / 98.20 | 1.2031 | N/A | 0 / 1088 |
| 32 / ZH / 42 | Main | 234.55 | 135.54 / 179.80 | 69.30 / 98.70 | 0.6173 | N/A | 0 / 2020 |
| 32 / ZH / 42 | PR | 233.71 | 135.92 / 181.89 | 67.80 / 96.40 | 0.6053 | N/A | 0 / 2020 |
| 32 / ZH / 43 | Main | 231.48 | 136.64 / 180.77 | 70.40 / 98.60 | 0.6173 | N/A | 0 / 2020 |
| 32 / ZH / 43 | PR | 231.78 | 137.00 / 186.76 | 68.80 / 96.90 | 0.6173 | N/A | 0 / 2020 |
| 64 / EN / 42 | Main | 260.07 | 240.76 / 352.07 | 112.00 / 228.70 | 1.2031 | N/A | 0 / 1088 |
| 64 / EN / 42 | PR | 277.39 | 226.59 / 353.81 | 108.90 / 186.40 | 1.2182 | N/A | 0 / 1088 |
| 64 / EN / 43 | Main | 260.50 | 242.09 / 381.05 | 118.50 / 289.70 | 1.2031 | N/A | 0 / 1088 |
| 64 / EN / 43 | PR | 259.83 | 229.52 / 357.70 | 107.90 / 261.70 | 1.2182 | N/A | 0 / 1088 |
| 64 / ZH / 42 | Main | 278.12 | 226.83 / 384.06 | 104.40 / 192.10 | 0.6203 | N/A | 0 / 2020 |
| 64 / ZH / 42 | PR | 286.40 | 220.17 / 332.08 | 103.40 / 197.90 | 0.6173 | N/A | 0 / 2020 |
| 64 / ZH / 43 | Main | 270.64 | 233.10 / 432.48 | 115.30 / 210.60 | 0.6263 | N/A | 0 / 2020 |
| 64 / ZH / 43 | PR | 280.97 | 225.92 / 363.16 | 110.60 / 215.20 | 0.6203 | N/A | 0 / 2020 |

Observed PR-minus-main ranges by concurrency (all four language/seed pairs):

- C1: p95 latency -2.17 to +0.21 ms; WER +0.0000 to +0.0000 percentage points. Mean first-text latency -1.20 to -0.50 ms.
- C16: p95 latency -1.30 to +1.47 ms; WER -0.0076 to +0.0060 percentage points. Mean first-text latency -2.20 to -1.30 ms.
- C32: p95 latency -5.62 to +13.15 ms; WER -0.0120 to +0.0000 percentage points. Mean first-text latency -5.20 to -1.50 ms.
- C64: p95 latency -69.33 to +1.74 ms; WER -0.0060 to +0.0151 percentage points. Mean first-text latency -10.60 to -1.00 ms.

## Costs

Startup is the two-seed mean from process launch through health-ready, including model/graph initialization and excluding downloads and explicit full-workload warmup (`--skip-server-warmup`). Peak VRAM is the maximum device-memory sample at 0.5-second intervals. Graph counts are successful `torch.cuda.CUDAGraph` captures whose owning objects remain live after scoring; both arms use the same observer.

| C / mode / metric | Main | PR | Delta |
| --- | ---: | ---: | ---: |
| 1 / nonstream / Startup (s) | 75.59 | 74.59 | -1.00 |
| 1 / nonstream / Peak VRAM (GiB) | 70.80 | 70.79 | -0.00 |
| 1 / nonstream / Live captures (42,43) | 1468, 1468 | 1468, 1468 | +0, +0 |
| 1 / stream / Startup (s) | 74.85 | 74.60 | -0.25 |
| 1 / stream / Peak VRAM (GiB) | 70.80 | 70.79 | -0.00 |
| 1 / stream / Live captures (42,43) | 1468, 1468 | 1468, 1468 | +0, +0 |
| 16 / nonstream / Startup (s) | 75.85 | 75.60 | -0.26 |
| 16 / nonstream / Peak VRAM (GiB) | 71.57 | 71.58 | +0.01 |
| 16 / nonstream / Live captures (42,43) | 1468, 1468 | 1468, 1468 | +0, +0 |
| 16 / stream / Startup (s) | 75.09 | 75.35 | +0.26 |
| 16 / stream / Peak VRAM (GiB) | 71.57 | 71.44 | -0.13 |
| 16 / stream / Live captures (42,43) | 1468, 1468 | 1468, 1468 | +0, +0 |
| 32 / nonstream / Startup (s) | 76.35 | 75.85 | -0.50 |
| 32 / nonstream / Peak VRAM (GiB) | 71.99 | 71.61 | -0.38 |
| 32 / nonstream / Live captures (42,43) | 1468, 1468 | 1468, 1468 | +0, +0 |
| 32 / stream / Startup (s) | 75.10 | 75.61 | +0.51 |
| 32 / stream / Peak VRAM (GiB) | 71.80 | 71.65 | -0.15 |
| 32 / stream / Live captures (42,43) | 1468, 1468 | 1468, 1468 | +0, +0 |
| 64 / nonstream / Startup (s) | 75.10 | 76.60 | +1.50 |
| 64 / nonstream / Peak VRAM (GiB) | 71.82 | 71.81 | -0.01 |
| 64 / nonstream / Live captures (42,43) | 1468, 1468 | 1468, 1468 | +0, +0 |
| 64 / stream / Startup (s) | 74.85 | 75.09 | +0.24 |
| 64 / stream / Peak VRAM (GiB) | 71.98 | 72.00 | +0.01 |
| 64 / stream / Live captures (42,43) | 1468, 1468 | 1468, 1468 | +0, +0 |

## Tests

- **Reviewer approval obtained for current head** `2cad1780`: db-ol approved on 2026-10-19T22:21:47Z, noting the explicit-override/fallback scope and passed CI. The post-merge final-source comparison on the changed baseline remains pending; the old measured source/base is kept explicit above.
- Review-fix source: **136 CPU tests and 3 accelerator tests passed** on the assigned H100; logs and source identities are in the evidence link.
- `pre-commit run --all-files`: passed. Complete diff versus the frozen main contains no `doc/` or `docs/` changes.
- Current-head [Omni CI](https://github.com/sgl-project/sglang-omni/actions/runs/39282431325) passed (attempt 2). Existing labels: `run-asr-ci` + `run-asr-qwen3-asr-1.7b`; preflight selected `run_asr=true`, `asr_ci_model=qwen3`, and stage-2 logs confirm **Qwen/Qwen3-ASR-1.7B**. Unit, accelerator, MOSS-TD prerequisite and Qwen SeedTTS stages passed; unselected stages are not hardware-validation evidence.
- Current-head ordinary CI: **9031 passed, 86 skipped**; accelerator CI: **769 passed, 15 skipped**. Tested synthetic merge revisions and logs are archived in the evidence.
- CPU/XPU workflow gate retries passed after the initial lint-wait cancellations. Intel CPU/XPU tests were skipped by the unchanged stage selection; this is gate recovery, not Intel hardware validation.
- Review-fix CI has passed. The completed paired performance and cost tables above retain their measured source identities; remaining review-fix performance qualification is separate from those completed measurements.

Developed by an autonomous research agent using [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) in [OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index), with co-author [Kangda Wei (@WeiKangda)](https://github.com/WeiKangda); [qualification and historical evidence](https://github.com/Zhuofeng-Li/sglang-omni/tree/codex/omni-review-evidence-20261019/pr-2882).
