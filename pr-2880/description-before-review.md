## Changes

- Capture full LM prefill on NVIDIA CUDA, with eager fallback for unsupported batches.
- Capture decode metadata with thread-local stream capture; keep FA3-only eligibility, metadata refresh and capture-failure recovery.
- Use exact-size decode graph buckets while preserving explicit operator bucket overrides.

**Changed defaults**

- NVIDIA CUDA prefill backend: `breakable` → `full`, with `full_prefill_max_req=32`.
- Qwen3-ASR stage default: `SGLANG_ENABLE_METADATA_GLUE_GRAPH=1`; operators can set `0`. Runtime eligibility still requires FA3 for both prefill and decode.
- Default CUDA decode buckets become every size from 1 through `cuda_graph_max_bs`; graph-disabled and explicitly customized configurations retain their policy.

## Paired comparison on current main

Concurrency sweep at **C1, C16, C32 and C64**, with each PR evaluated independently. C32 was measured on 2026-10-17; C1/C16/C64 were measured on 2026-10-18. All tables use the same frozen measured main `8fff1e0e8c99a710afe876d1514209e1157c5502` and PR `fa422fedf48ec76233859ef173cb7bc1272c4952`. Latest upstream main observed at 2026-10-18T20:23:39.008260+00:00: `3a0655b84813b7d855d6bf042864b9ceaeb7a062`. The tables describe the frozen measured commit above.

- Single NVIDIA H100 80GB HBM3 per cohort. C1/C16/C64 use GPU `GPU-6a051904-54a1-9fbc-ed92-1c8ea133e232`; the reused C32 data uses `GPU-8c2e7fe8-6622-46fc-374a-1b0bea3c1a31`. Each main/PR pair runs on the same physical card. Cross-concurrency comparisons also include this card/date difference.
- Supplementary runs resolve both prefill and decode attention to **FA3**; representative main/PR startup logs were checked for all three PRs.
- CUDA 13.0 / Torch 2.13.0+cu130 / SGLang 0.5.21 / Transformers 5.12.1; model `Qwen/Qwen3-ASR-1.7B@7278e1e70fe206f11671096ffdd38061171dd6e5`, BF16. Dataset `zhaochenyang20/seed-tts-eval-arrow@27f4c1adee83b5b29b7c4b375f6b976324bda308`: complete EN (1,088) and ZH (2,020) splits.
- YAML: `results/pr2880-c<C>-<mode>-<arm>-seed<seed>/config.yaml`, using the frozen source's `Qwen3ASRPipelineConfig`. Overrides: model path `/qualification/assets/model`, ASR GPU 0; factory `dtype=bfloat16`, `pre_lm_cache_size_bytes=1`, `mm_embedding_cache_size_bytes=0`; engine `disable_radix_cache=true`, `random_seed=<seed>`. Greedy decoding and default duration-dependent output budget (128-token floor); no client token override. Full configurations and hashes are in the evidence link.
- For **each concurrency and mode**, seeds 42/43 use **main(42) → PR(42) → PR(43) → main(43)**. Seeds control sample shuffle, Python hash seed and engine RNG; paired sample-order hashes match. Every cohort starts a fresh service with empty compiler caches, then performs one full warmup and one scored pass per language. CPU uses the same default shared scheduling without quota/affinity changes.
- Each row below is an individual scored pass. Latencies are mean/p95 milliseconds per pass; percentiles are never pooled or averaged. Summary throughput is the geometric mean of EN/ZH PR/main ratios after averaging req/s across the two seeds within each language. Two seeds do not establish statistical significance. WER is corpus WER (ZH uses character tokens). SIM is N/A because ASR produces text. Streaming first text means the first nonempty delta; exact delta/final-text agreement and terminal DONE are checked.

### Non-streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | +0.67% |
| 16 | +0.17% |
| 32 | +4.08% |
| 64 | +1.95% |

| C / split / seed | Arm | req/s | Latency mean / p95 (ms) | First text mean / p95 (ms) | WER (%) | SIM | Failed / attempted |
| --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 / EN / 42 | Main | 24.55 | 40.59 / 49.53 | N/A: completed response | 1.2258 | N/A | 0 / 1088 |
| 1 / EN / 42 | PR | 24.48 | 40.68 / 49.73 | N/A: completed response | 1.2258 | N/A | 0 / 1088 |
| 1 / EN / 43 | Main | 24.42 | 40.81 / 49.54 | N/A: completed response | 1.2258 | N/A | 0 / 1088 |
| 1 / EN / 43 | PR | 24.49 | 40.70 / 49.84 | N/A: completed response | 1.2258 | N/A | 0 / 1088 |
| 1 / ZH / 42 | Main | 26.92 | 36.96 / 46.79 | N/A: completed response | 0.5933 | N/A | 0 / 2020 |
| 1 / ZH / 42 | PR | 27.08 | 36.79 / 46.80 | N/A: completed response | 0.5933 | N/A | 0 / 2020 |
| 1 / ZH / 43 | Main | 26.69 | 37.34 / 47.40 | N/A: completed response | 0.5933 | N/A | 0 / 2020 |
| 1 / ZH / 43 | PR | 27.24 | 36.58 / 46.47 | N/A: completed response | 0.5933 | N/A | 0 / 2020 |
| 16 / EN / 42 | Main | 147.85 | 107.34 / 139.62 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 16 / EN / 42 | PR | 148.44 | 106.94 / 140.46 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 16 / EN / 43 | Main | 148.13 | 106.91 / 138.83 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 16 / EN / 43 | PR | 149.38 | 106.47 / 139.06 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 16 / ZH / 42 | Main | 154.67 | 102.65 / 138.51 | N/A: completed response | 0.5933 | N/A | 0 / 2020 |
| 16 / ZH / 42 | PR | 156.46 | 101.76 / 138.35 | N/A: completed response | 0.5963 | N/A | 0 / 2020 |
| 16 / ZH / 43 | Main | 159.15 | 100.03 / 135.87 | N/A: completed response | 0.6053 | N/A | 0 / 2020 |
| 16 / ZH / 43 | PR | 156.52 | 101.40 / 137.26 | N/A: completed response | 0.5933 | N/A | 0 / 2020 |
| 32 / EN / 42 | Main | 224.64 | 140.27 / 178.27 | N/A: completed response | 1.2182 | N/A | 0 / 1088 |
| 32 / EN / 42 | PR | 231.68 | 136.42 / 173.36 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 32 / EN / 43 | Main | 223.80 | 140.91 / 183.30 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 32 / EN / 43 | PR | 232.43 | 135.94 / 177.07 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 32 / ZH / 42 | Main | 239.51 | 132.49 / 174.18 | N/A: completed response | 0.5993 | N/A | 0 / 2020 |
| 32 / ZH / 42 | PR | 250.80 | 126.63 / 168.37 | N/A: completed response | 0.6023 | N/A | 0 / 2020 |
| 32 / ZH / 43 | Main | 232.45 | 136.69 / 192.60 | N/A: completed response | 0.6083 | N/A | 0 / 2020 |
| 32 / ZH / 43 | PR | 243.22 | 130.72 / 172.99 | N/A: completed response | 0.6023 | N/A | 0 / 2020 |
| 64 / EN / 42 | Main | 288.76 | 215.91 / 294.22 | N/A: completed response | 1.2182 | N/A | 0 / 1088 |
| 64 / EN / 42 | PR | 305.54 | 205.46 / 279.90 | N/A: completed response | 1.2107 | N/A | 0 / 1088 |
| 64 / EN / 43 | Main | 300.32 | 208.51 / 277.12 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 64 / EN / 43 | PR | 299.22 | 208.24 / 279.75 | N/A: completed response | 1.2182 | N/A | 0 / 1088 |
| 64 / ZH / 42 | Main | 296.26 | 212.52 / 300.52 | N/A: completed response | 0.6053 | N/A | 0 / 2020 |
| 64 / ZH / 42 | PR | 303.84 | 208.73 / 339.91 | N/A: completed response | 0.6173 | N/A | 0 / 2020 |
| 64 / ZH / 43 | Main | 301.65 | 209.00 / 317.40 | N/A: completed response | 0.6053 | N/A | 0 / 2020 |
| 64 / ZH / 43 | PR | 301.48 | 209.69 / 317.71 | N/A: completed response | 0.6113 | N/A | 0 / 2020 |

Observed PR-minus-main ranges by concurrency (all four language/seed pairs):

- C1: p95 latency -0.93 to +0.29 ms; WER +0.0000 to +0.0000 percentage points.
- C16: p95 latency -0.16 to +1.39 ms; WER -0.0120 to +0.0030 percentage points.
- C32: p95 latency -19.61 to -4.91 ms; WER -0.0151 to +0.0030 percentage points.
- C64: p95 latency -14.32 to +39.39 ms; WER -0.0076 to +0.0151 percentage points.

### Streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | -0.01% |
| 16 | -0.69% |
| 32 | +1.32% |
| 64 | +4.57% |

| C / split / seed | Arm | req/s | Latency mean / p95 (ms) | First text mean / p95 (ms) | WER (%) | SIM | Failed / attempted |
| --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 / EN / 42 | Main | 24.63 | 40.36 / 49.38 | 12.10 / 13.50 | 1.2258 | N/A | 0 / 1088 |
| 1 / EN / 42 | PR | 24.72 | 40.33 / 49.58 | 11.80 / 13.00 | 1.2258 | N/A | 0 / 1088 |
| 1 / EN / 43 | Main | 24.81 | 40.16 / 49.19 | 12.00 / 13.20 | 1.2258 | N/A | 0 / 1088 |
| 1 / EN / 43 | PR | 24.72 | 40.32 / 49.87 | 11.70 / 13.10 | 1.2258 | N/A | 0 / 1088 |
| 1 / ZH / 42 | Main | 27.04 | 36.85 / 46.73 | 11.90 / 12.90 | 0.5933 | N/A | 0 / 2020 |
| 1 / ZH / 42 | PR | 27.15 | 36.71 / 46.80 | 11.50 / 12.40 | 0.5933 | N/A | 0 / 2020 |
| 1 / ZH / 43 | Main | 27.30 | 36.44 / 46.39 | 11.50 / 12.40 | 0.5933 | N/A | 0 / 2020 |
| 1 / ZH / 43 | PR | 27.19 | 36.65 / 46.87 | 11.40 / 12.30 | 0.5933 | N/A | 0 / 2020 |
| 16 / EN / 42 | Main | 146.26 | 108.79 / 142.80 | 57.70 / 79.60 | 1.2031 | N/A | 0 / 1088 |
| 16 / EN / 42 | PR | 146.55 | 108.49 / 144.01 | 59.20 / 81.00 | 1.2031 | N/A | 0 / 1088 |
| 16 / EN / 43 | Main | 145.59 | 107.90 / 142.60 | 58.00 / 82.90 | 1.2031 | N/A | 0 / 1088 |
| 16 / EN / 43 | PR | 143.78 | 110.58 / 147.29 | 62.40 / 86.40 | 1.2107 | N/A | 0 / 1088 |
| 16 / ZH / 42 | Main | 152.56 | 104.14 / 139.78 | 60.10 / 79.60 | 0.5904 | N/A | 0 / 2020 |
| 16 / ZH / 42 | PR | 151.87 | 104.82 / 140.86 | 60.90 / 80.30 | 0.5933 | N/A | 0 / 2020 |
| 16 / ZH / 43 | Main | 153.69 | 103.36 / 139.47 | 59.10 / 79.90 | 0.6023 | N/A | 0 / 2020 |
| 16 / ZH / 43 | PR | 151.73 | 104.97 / 139.74 | 62.60 / 81.90 | 0.5963 | N/A | 0 / 2020 |
| 32 / EN / 42 | Main | 211.12 | 148.91 / 185.47 | 78.50 / 101.20 | 1.2107 | N/A | 0 / 1088 |
| 32 / EN / 42 | PR | 213.27 | 148.15 / 195.79 | 79.40 / 109.40 | 1.2107 | N/A | 0 / 1088 |
| 32 / EN / 43 | Main | 221.79 | 142.95 / 183.79 | 71.90 / 100.30 | 1.2107 | N/A | 0 / 1088 |
| 32 / EN / 43 | PR | 224.71 | 140.40 / 179.60 | 72.30 / 101.00 | 1.2031 | N/A | 0 / 1088 |
| 32 / ZH / 42 | Main | 238.22 | 133.10 / 175.37 | 67.90 / 96.80 | 0.6053 | N/A | 0 / 2020 |
| 32 / ZH / 42 | PR | 242.27 | 130.79 / 171.64 | 68.30 / 97.10 | 0.5993 | N/A | 0 / 2020 |
| 32 / ZH / 43 | Main | 228.71 | 138.91 / 186.18 | 71.90 / 102.10 | 0.6083 | N/A | 0 / 2020 |
| 32 / ZH / 43 | PR | 231.56 | 135.13 / 178.37 | 73.00 / 100.50 | 0.6053 | N/A | 0 / 2020 |
| 64 / EN / 42 | Main | 263.64 | 237.32 / 384.77 | 110.00 / 264.10 | 1.2182 | N/A | 0 / 1088 |
| 64 / EN / 42 | PR | 268.18 | 230.40 / 384.74 | 109.80 / 289.00 | 1.2182 | N/A | 0 / 1088 |
| 64 / EN / 43 | Main | 269.97 | 231.68 / 363.47 | 114.00 / 202.70 | 1.2182 | N/A | 0 / 1088 |
| 64 / EN / 43 | PR | 278.67 | 225.46 / 387.28 | 103.50 / 254.90 | 1.2258 | N/A | 0 / 1088 |
| 64 / ZH / 42 | Main | 282.53 | 223.62 / 351.02 | 103.60 / 198.70 | 0.6173 | N/A | 0 / 2020 |
| 64 / ZH / 42 | PR | 291.77 | 217.10 / 343.46 | 104.90 / 209.10 | 0.6053 | N/A | 0 / 2020 |
| 64 / ZH / 43 | Main | 265.72 | 237.57 / 471.07 | 120.10 / 234.20 | 0.6053 | N/A | 0 / 2020 |
| 64 / ZH / 43 | PR | 293.23 | 215.31 / 353.25 | 105.30 / 213.20 | 0.6173 | N/A | 0 / 2020 |

Observed PR-minus-main ranges by concurrency (all four language/seed pairs):

- C1: p95 latency +0.07 to +0.68 ms; WER +0.0000 to +0.0000 percentage points. Mean first-text latency -0.40 to -0.10 ms.
- C16: p95 latency +0.27 to +4.70 ms; WER -0.0060 to +0.0076 percentage points. Mean first-text latency +0.80 to +4.40 ms.
- C32: p95 latency -7.81 to +10.31 ms; WER -0.0076 to +0.0000 percentage points. Mean first-text latency +0.40 to +1.10 ms.
- C64: p95 latency -117.82 to +23.81 ms; WER -0.0120 to +0.0120 percentage points. Mean first-text latency -14.80 to +1.30 ms.

## Costs

Startup is the two-seed mean from process launch through health-ready, including model/graph initialization and excluding downloads and explicit full-workload warmup (`--skip-server-warmup`). Peak VRAM is the maximum device-memory sample at 0.5-second intervals. Graph counts are successful `torch.cuda.CUDAGraph` captures whose owning objects remain live after scoring; both arms use the same observer.

| C / mode / metric | Main | PR | Delta |
| --- | ---: | ---: | ---: |
| 1 / nonstream / Startup (s) | 75.85 | 77.60 | +1.75 |
| 1 / nonstream / Peak VRAM (GiB) | 70.80 | 70.78 | -0.02 |
| 1 / nonstream / Live captures (42,43) | 1468, 1468 | 121, 121 | -1347, -1347 |
| 1 / stream / Startup (s) | 75.10 | 76.09 | +0.99 |
| 1 / stream / Peak VRAM (GiB) | 70.80 | 70.78 | -0.02 |
| 1 / stream / Live captures (42,43) | 1468, 1468 | 121, 121 | -1347, -1347 |
| 16 / nonstream / Startup (s) | 75.35 | 75.60 | +0.25 |
| 16 / nonstream / Peak VRAM (GiB) | 71.58 | 71.58 | -0.00 |
| 16 / nonstream / Live captures (42,43) | 1468, 1468 | 136, 136 | -1332, -1332 |
| 16 / stream / Startup (s) | 75.35 | 76.34 | +1.00 |
| 16 / stream / Peak VRAM (GiB) | 71.60 | 71.58 | -0.02 |
| 16 / stream / Live captures (42,43) | 1468, 1468 | 136, 136 | -1332, -1332 |
| 32 / nonstream / Startup (s) | 75.35 | 77.10 | +1.75 |
| 32 / nonstream / Peak VRAM (GiB) | 72.12 | 72.16 | +0.03 |
| 32 / nonstream / Live captures (42,43) | 1468, 1468 | 152, 152 | -1316, -1316 |
| 32 / stream / Startup (s) | 77.10 | 76.85 | -0.25 |
| 32 / stream / Peak VRAM (GiB) | 71.94 | 71.70 | -0.24 |
| 32 / stream / Live captures (42,43) | 1468, 1468 | 152, 152 | -1316, -1316 |
| 64 / nonstream / Startup (s) | 75.09 | 76.85 | +1.76 |
| 64 / nonstream / Peak VRAM (GiB) | 72.04 | 72.11 | +0.07 |
| 64 / nonstream / Live captures (42,43) | 1468, 1468 | 183, 181 | -1285, -1287 |
| 64 / stream / Startup (s) | 76.08 | 77.83 | +1.75 |
| 64 / stream / Peak VRAM (GiB) | 72.17 | 72.32 | +0.14 |
| 64 / stream / Live captures (42,43) | 1468, 1468 | 180, 183 | -1288, -1285 |

## Tests

- Frozen-main integrated source CPU regression tests (2026-10-17): `135 passed, 4 deselected, 16 warnings in 20.71s`.
- Added metadata capture/replay, live-input refresh and failure-recovery cases in `test_metadata_glue.py`; added bucket-override, FA3 eligibility and full/exact-size graph pipeline cases.
- CI labels: `run-asr-ci` + `run-asr-qwen3-asr-1.7b`. The current head's preflight explicitly resolved `run_asr=true`, `asr_ci_model=qwen3`.
- `pre-commit run --all-files`: passed on a checkout with the same source tree.
- Current-head [Omni CI](https://github.com/sgl-project/sglang-omni/actions/runs/39051389350): **success**; head `fa422fedf48ec76233859ef173cb7bc1272c4952`.
- Current-head GPU regression cases: **4 Qwen3-ASR accelerator cases passed** in [the GPU unit job](https://github.com/sgl-project/sglang-omni/actions/runs/39051389350/job/117451299341). The job passed after the repository runner automatically retried an earlier failure; the job log retains that attempt.

Developed by an autonomous research agent using [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) in [OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index), with co-author [Kangda Wei (@WeiKangda)](https://github.com/WeiKangda); [historical experiments and calibration](https://github.com/sgl-project/sglang-omni/pull/2880#issuecomment-6254716086).
