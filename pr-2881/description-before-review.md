## Changes

- Allow eligible whole-prompt ASR prefill to use launch/resolve lookahead, and finish prefill bookkeeping before publishing tokens.
- Use linear ASR positions, drain independently finished request builds, and move the admission wait to prefill release for the opt-in path.
- Preserve exclusions for sessions, chunked/mixed batches, speculative execution, prefill-only and logprob batches.

**Changed defaults**

- Qwen3-ASR on NVIDIA CUDA passes `async_prefill=True` to the scheduler; the shared scheduler default remains opt-out.
- CUDA ASR setup disables per-step MRoPE-position reconstruction. Request-build/coalescing numeric defaults are unchanged.

## Paired comparison on current main

Concurrency sweep at **C1, C16, C32 and C64**, with each PR evaluated independently. C32 was measured on 2026-10-17; C1/C16/C64 were measured on 2026-10-18. All tables use the same frozen measured main `8fff1e0e8c99a710afe876d1514209e1157c5502` and PR `a38a1f30c1a0ca56239da0580b9da7c6735e3780`. Latest upstream main observed at 2026-10-18T20:23:39.008260+00:00: `3a0655b84813b7d855d6bf042864b9ceaeb7a062`. The tables describe the frozen measured commit above.

- Single NVIDIA H100 80GB HBM3 per cohort. C1/C16/C64 use GPU `GPU-6a051904-54a1-9fbc-ed92-1c8ea133e232`; the reused C32 data uses `GPU-8c2e7fe8-6622-46fc-374a-1b0bea3c1a31`. Each main/PR pair runs on the same physical card. Cross-concurrency comparisons also include this card/date difference.
- Supplementary runs resolve both prefill and decode attention to **FA3**; representative main/PR startup logs were checked for all three PRs.
- CUDA 13.0 / Torch 2.13.0+cu130 / SGLang 0.5.21 / Transformers 5.12.1; model `Qwen/Qwen3-ASR-1.7B@7278e1e70fe206f11671096ffdd38061171dd6e5`, BF16. Dataset `zhaochenyang20/seed-tts-eval-arrow@27f4c1adee83b5b29b7c4b375f6b976324bda308`: complete EN (1,088) and ZH (2,020) splits.
- YAML: `results/pr2881-c<C>-<mode>-<arm>-seed<seed>/config.yaml`, using the frozen source's `Qwen3ASRPipelineConfig`. Overrides: model path `/qualification/assets/model`, ASR GPU 0; factory `dtype=bfloat16`, `pre_lm_cache_size_bytes=1`, `mm_embedding_cache_size_bytes=0`; engine `disable_radix_cache=true`, `random_seed=<seed>`. Greedy decoding and default duration-dependent output budget (128-token floor); no client token override. Full configurations and hashes are in the evidence link.
- For **each concurrency and mode**, seeds 42/43 use **main(42) → PR(42) → PR(43) → main(43)**. Seeds control sample shuffle, Python hash seed and engine RNG; paired sample-order hashes match. Every cohort starts a fresh service with empty compiler caches, then performs one full warmup and one scored pass per language. CPU uses the same default shared scheduling without quota/affinity changes.
- Each row below is an individual scored pass. Latencies are mean/p95 milliseconds per pass; percentiles are never pooled or averaged. Summary throughput is the geometric mean of EN/ZH PR/main ratios after averaging req/s across the two seeds within each language. Two seeds do not establish statistical significance. WER is corpus WER (ZH uses character tokens). SIM is N/A because ASR produces text. Streaming first text means the first nonempty delta; exact delta/final-text agreement and terminal DONE are checked.

### Non-streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | +0.43% |
| 16 | +4.53% |
| 32 | +6.11% |
| 64 | +9.14% |

| C / split / seed | Arm | req/s | Latency mean / p95 (ms) | First text mean / p95 (ms) | WER (%) | SIM | Failed / attempted |
| --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 / EN / 42 | Main | 24.46 | 40.74 / 49.83 | N/A: completed response | 1.2258 | N/A | 0 / 1088 |
| 1 / EN / 42 | PR | 24.69 | 40.37 / 49.37 | N/A: completed response | 1.2258 | N/A | 0 / 1088 |
| 1 / EN / 43 | Main | 24.65 | 40.45 / 49.40 | N/A: completed response | 1.2258 | N/A | 0 / 1088 |
| 1 / EN / 43 | PR | 24.67 | 40.39 / 49.41 | N/A: completed response | 1.2258 | N/A | 0 / 1088 |
| 1 / ZH / 42 | Main | 26.94 | 36.94 / 46.88 | N/A: completed response | 0.5933 | N/A | 0 / 2020 |
| 1 / ZH / 42 | PR | 27.06 | 36.82 / 46.83 | N/A: completed response | 0.5933 | N/A | 0 / 2020 |
| 1 / ZH / 43 | Main | 27.05 | 36.84 / 46.88 | N/A: completed response | 0.5933 | N/A | 0 / 2020 |
| 1 / ZH / 43 | PR | 27.12 | 36.75 / 46.65 | N/A: completed response | 0.5933 | N/A | 0 / 2020 |
| 16 / EN / 42 | Main | 148.66 | 106.70 / 137.60 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 16 / EN / 42 | PR | 154.75 | 102.50 / 131.57 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 16 / EN / 43 | Main | 149.80 | 106.12 / 139.59 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 16 / EN / 43 | PR | 155.97 | 101.81 / 131.95 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 16 / ZH / 42 | Main | 155.06 | 102.72 / 137.62 | N/A: completed response | 0.5904 | N/A | 0 / 2020 |
| 16 / ZH / 42 | PR | 162.99 | 97.59 / 130.73 | N/A: completed response | 0.5933 | N/A | 0 / 2020 |
| 16 / ZH / 43 | Main | 155.89 | 102.25 / 135.57 | N/A: completed response | 0.5963 | N/A | 0 / 2020 |
| 16 / ZH / 43 | PR | 163.37 | 97.47 / 130.64 | N/A: completed response | 0.6113 | N/A | 0 / 2020 |
| 32 / EN / 42 | Main | 224.43 | 140.69 / 184.56 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 32 / EN / 42 | PR | 246.39 | 127.86 / 166.13 | N/A: completed response | 1.2107 | N/A | 0 / 1088 |
| 32 / EN / 43 | Main | 229.13 | 138.14 / 178.01 | N/A: completed response | 1.2182 | N/A | 0 / 1088 |
| 32 / EN / 43 | PR | 228.97 | 137.97 / 250.46 | N/A: completed response | 1.2031 | N/A | 0 / 1088 |
| 32 / ZH / 42 | Main | 237.84 | 131.80 / 174.86 | N/A: completed response | 0.6053 | N/A | 0 / 2020 |
| 32 / ZH / 42 | PR | 256.45 | 123.50 / 163.76 | N/A: completed response | 0.6173 | N/A | 0 / 2020 |
| 32 / ZH / 43 | Main | 244.21 | 128.59 / 168.44 | N/A: completed response | 0.6083 | N/A | 0 / 2020 |
| 32 / ZH / 43 | PR | 261.44 | 120.37 / 158.17 | N/A: completed response | 0.6053 | N/A | 0 / 2020 |
| 64 / EN / 42 | Main | 293.34 | 213.90 / 291.73 | N/A: completed response | 1.2107 | N/A | 0 / 1088 |
| 64 / EN / 42 | PR | 316.51 | 194.50 / 263.17 | N/A: completed response | 1.2182 | N/A | 0 / 1088 |
| 64 / EN / 43 | Main | 296.32 | 211.72 / 286.46 | N/A: completed response | 1.2182 | N/A | 0 / 1088 |
| 64 / EN / 43 | PR | 319.46 | 194.47 / 269.48 | N/A: completed response | 1.2107 | N/A | 0 / 1088 |
| 64 / ZH / 42 | Main | 290.96 | 217.84 / 290.35 | N/A: completed response | 0.6263 | N/A | 0 / 2020 |
| 64 / ZH / 42 | PR | 320.30 | 196.12 / 340.02 | N/A: completed response | 0.6203 | N/A | 0 / 2020 |
| 64 / ZH / 43 | Main | 294.57 | 214.46 / 308.18 | N/A: completed response | 0.6203 | N/A | 0 / 2020 |
| 64 / ZH / 43 | PR | 326.37 | 193.52 / 274.70 | N/A: completed response | 0.6173 | N/A | 0 / 2020 |

Observed PR-minus-main ranges by concurrency (all four language/seed pairs):

- C1: p95 latency -0.46 to +0.01 ms; WER +0.0000 to +0.0000 percentage points.
- C16: p95 latency -7.64 to -4.93 ms; WER +0.0000 to +0.0150 percentage points.
- C32: p95 latency -18.44 to +72.45 ms; WER -0.0151 to +0.0120 percentage points.
- C64: p95 latency -33.47 to +49.67 ms; WER -0.0076 to +0.0076 percentage points.

### Streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | -0.08% |
| 16 | +8.43% |
| 32 | +9.49% |
| 64 | +10.98% |

| C / split / seed | Arm | req/s | Latency mean / p95 (ms) | First text mean / p95 (ms) | WER (%) | SIM | Failed / attempted |
| --- | --- | ---: | ---: | --- | ---: | --- | --- |
| 1 / EN / 42 | Main | 24.66 | 40.40 / 49.42 | 12.10 / 13.50 | 1.2258 | N/A | 0 / 1088 |
| 1 / EN / 42 | PR | 24.69 | 40.37 / 49.28 | 12.90 / 14.10 | 1.2258 | N/A | 0 / 1088 |
| 1 / EN / 43 | Main | 25.07 | 39.78 / 48.56 | 11.80 / 13.20 | 1.2258 | N/A | 0 / 1088 |
| 1 / EN / 43 | PR | 25.01 | 39.85 / 48.79 | 12.80 / 14.10 | 1.2258 | N/A | 0 / 1088 |
| 1 / ZH / 42 | Main | 27.21 | 36.62 / 46.52 | 11.70 / 12.60 | 0.5933 | N/A | 0 / 2020 |
| 1 / ZH / 42 | PR | 27.21 | 36.61 / 46.55 | 12.50 / 13.40 | 0.5933 | N/A | 0 / 2020 |
| 1 / ZH / 43 | Main | 27.42 | 36.34 / 46.17 | 11.70 / 12.50 | 0.5933 | N/A | 0 / 2020 |
| 1 / ZH / 43 | PR | 27.36 | 36.42 / 46.32 | 12.80 / 13.60 | 0.5933 | N/A | 0 / 2020 |
| 16 / EN / 42 | Main | 147.40 | 107.83 / 142.40 | 57.90 / 80.90 | 1.2107 | N/A | 0 / 1088 |
| 16 / EN / 42 | PR | 153.84 | 102.98 / 138.29 | 62.50 / 85.20 | 1.2031 | N/A | 0 / 1088 |
| 16 / EN / 43 | Main | 144.97 | 107.98 / 141.73 | 57.70 / 82.70 | 1.2107 | N/A | 0 / 1088 |
| 16 / EN / 43 | PR | 155.49 | 102.19 / 136.08 | 62.70 / 85.10 | 1.2107 | N/A | 0 / 1088 |
| 16 / ZH / 42 | Main | 151.77 | 104.74 / 139.93 | 59.00 / 79.40 | 0.5933 | N/A | 0 / 2020 |
| 16 / ZH / 42 | PR | 166.77 | 95.55 / 129.94 | 61.40 / 83.50 | 0.5993 | N/A | 0 / 2020 |
| 16 / ZH / 43 | Main | 153.78 | 103.62 / 139.34 | 59.20 / 79.50 | 0.6143 | N/A | 0 / 2020 |
| 16 / ZH / 43 | PR | 172.77 | 91.91 / 126.98 | 58.20 / 81.00 | 0.6023 | N/A | 0 / 2020 |
| 32 / EN / 42 | Main | 215.69 | 143.62 / 190.68 | 71.40 / 100.80 | 1.2031 | N/A | 0 / 1088 |
| 32 / EN / 42 | PR | 240.51 | 130.90 / 165.71 | 74.10 / 101.50 | 1.2107 | N/A | 0 / 1088 |
| 32 / EN / 43 | Main | 221.78 | 142.15 / 185.43 | 70.80 / 100.60 | 1.2031 | N/A | 0 / 1088 |
| 32 / EN / 43 | PR | 239.48 | 131.50 / 168.07 | 75.80 / 105.40 | 1.2107 | N/A | 0 / 1088 |
| 32 / ZH / 42 | Main | 231.18 | 135.27 / 180.83 | 70.40 / 98.00 | 0.6023 | N/A | 0 / 2020 |
| 32 / ZH / 42 | PR | 251.69 | 124.13 / 161.89 | 73.20 / 101.40 | 0.6053 | N/A | 0 / 2020 |
| 32 / ZH / 43 | Main | 229.93 | 137.62 / 182.16 | 71.50 / 100.30 | 0.5993 | N/A | 0 / 2020 |
| 32 / ZH / 43 | PR | 252.12 | 125.98 / 168.98 | 75.90 / 109.20 | 0.6173 | N/A | 0 / 2020 |
| 64 / EN / 42 | Main | 258.52 | 239.83 / 383.54 | 113.80 / 290.80 | 1.2182 | N/A | 0 / 1088 |
| 64 / EN / 42 | PR | 287.53 | 219.37 / 340.57 | 117.00 / 208.70 | 1.2182 | N/A | 0 / 1088 |
| 64 / EN / 43 | Main | 264.11 | 237.66 / 357.39 | 111.00 / 241.40 | 1.2258 | N/A | 0 / 1088 |
| 64 / EN / 43 | PR | 288.67 | 218.35 / 354.07 | 117.50 / 207.40 | 1.2182 | N/A | 0 / 1088 |
| 64 / ZH / 42 | Main | 280.61 | 225.18 / 358.39 | 108.90 / 191.70 | 0.6143 | N/A | 0 / 2020 |
| 64 / ZH / 42 | PR | 318.54 | 197.93 / 289.52 | 104.80 / 189.20 | 0.6203 | N/A | 0 / 2020 |
| 64 / ZH / 43 | Main | 277.61 | 227.26 / 370.76 | 109.50 / 283.50 | 0.6113 | N/A | 0 / 2020 |
| 64 / ZH / 43 | PR | 305.07 | 206.65 / 354.04 | 111.00 / 203.10 | 0.6173 | N/A | 0 / 2020 |

Observed PR-minus-main ranges by concurrency (all four language/seed pairs):

- C1: p95 latency -0.14 to +0.23 ms; WER +0.0000 to +0.0000 percentage points. Mean first-text latency +0.80 to +1.10 ms.
- C16: p95 latency -12.35 to -4.11 ms; WER -0.0120 to +0.0060 percentage points. Mean first-text latency -1.00 to +5.00 ms.
- C32: p95 latency -24.96 to -13.18 ms; WER +0.0030 to +0.0180 percentage points. Mean first-text latency +2.70 to +5.00 ms.
- C64: p95 latency -68.87 to -3.32 ms; WER -0.0076 to +0.0060 percentage points. Mean first-text latency -4.10 to +6.50 ms.

## Costs

Startup is the two-seed mean from process launch through health-ready, including model/graph initialization and excluding downloads and explicit full-workload warmup (`--skip-server-warmup`). Peak VRAM is the maximum device-memory sample at 0.5-second intervals. Graph counts are successful `torch.cuda.CUDAGraph` captures whose owning objects remain live after scoring; both arms use the same observer.

| C / mode / metric | Main | PR | Delta |
| --- | ---: | ---: | ---: |
| 1 / nonstream / Startup (s) | 76.10 | 75.85 | -0.24 |
| 1 / nonstream / Peak VRAM (GiB) | 70.80 | 70.80 | +0.00 |
| 1 / nonstream / Live captures (42,43) | 1468, 1468 | 1468, 1468 | +0, +0 |
| 1 / stream / Startup (s) | 76.85 | 75.85 | -1.00 |
| 1 / stream / Peak VRAM (GiB) | 70.80 | 70.80 | +0.00 |
| 1 / stream / Live captures (42,43) | 1468, 1468 | 1468, 1468 | +0, +0 |
| 16 / nonstream / Startup (s) | 75.10 | 75.34 | +0.24 |
| 16 / nonstream / Peak VRAM (GiB) | 71.57 | 71.58 | +0.01 |
| 16 / nonstream / Live captures (42,43) | 1468, 1468 | 1468, 1468 | +0, +0 |
| 16 / stream / Startup (s) | 75.60 | 74.85 | -0.75 |
| 16 / stream / Peak VRAM (GiB) | 71.58 | 72.06 | +0.48 |
| 16 / stream / Live captures (42,43) | 1468, 1468 | 1468, 1468 | +0, +0 |
| 32 / nonstream / Startup (s) | 75.85 | 75.09 | -0.75 |
| 32 / nonstream / Peak VRAM (GiB) | 71.96 | 72.11 | +0.15 |
| 32 / nonstream / Live captures (42,43) | 1468, 1468 | 1468, 1468 | +0, +0 |
| 32 / stream / Startup (s) | 77.11 | 77.10 | -0.00 |
| 32 / stream / Peak VRAM (GiB) | 71.78 | 71.78 | +0.00 |
| 32 / stream / Live captures (42,43) | 1468, 1468 | 1468, 1468 | +0, +0 |
| 64 / nonstream / Startup (s) | 75.09 | 75.35 | +0.26 |
| 64 / nonstream / Peak VRAM (GiB) | 71.98 | 71.99 | +0.01 |
| 64 / nonstream / Live captures (42,43) | 1468, 1468 | 1468, 1468 | +0, +0 |
| 64 / stream / Startup (s) | 74.35 | 74.35 | -0.00 |
| 64 / stream / Peak VRAM (GiB) | 72.17 | 71.84 | -0.33 |
| 64 / stream / Live captures (42,43) | 1468, 1468 | 1468, 1468 | +0, +0 |

## Tests

- Frozen-main integrated source CPU regression tests (2026-10-17): `127 passed, 3 deselected, 16 warnings in 19.73s`; `67 passed, 3 skipped, 16 warnings in 7.31s`.
- Added unsupported-prefill-batch rejection and prefill-hook ordering tests in `tests/unit_test/pipeline/test_async_decode.py`; updated native/MRoPE position fixtures.
- CI labels: `run-asr-ci` + `run-asr-qwen3-asr-1.7b`. The current head's preflight explicitly resolved `run_asr=true`, `asr_ci_model=qwen3`.
- `pre-commit run --all-files`: passed on a checkout with the same source tree.
- Current-head [Omni CI](https://github.com/sgl-project/sglang-omni/actions/runs/39051832402): **success**; head `a38a1f30c1a0ca56239da0580b9da7c6735e3780`.
- Current-head GPU regression cases: **3 Qwen3-ASR accelerator cases passed** in [the GPU unit job](https://github.com/sgl-project/sglang-omni/actions/runs/39051832402/job/117452703620).

Developed by an autonomous research agent using [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) in [OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index), with co-author [Kangda Wei (@WeiKangda)](https://github.com/WeiKangda); [historical experiments and calibration](https://github.com/sgl-project/sglang-omni/pull/2881#issuecomment-6254717205).
