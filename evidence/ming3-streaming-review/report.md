# Ming3 streaming review evidence

**Current-main follow-up:** the [fresh 0.5B measurement and both-model integration checks](current-main/report.md) use main `0fe60cf6` and integration `348f6973`. The tables below remain the original measurements; Tiny timings retain that original source.

Measurement blocks: **32/32**. All requested latency blocks are complete.

Measured integration: `251f02b467fe06269cb2d3d8c1063565d7c3de82`, tree `3e68505e3a2c26ae6e88e8360007bc0d3896d5d7`. The final dense head `8ca2534388574830fbfb3b692feee6851c57e0f2` has the identical tree. Tiny revision `5c955911` differs only in the companion dense enablement guard and its test. Then-published heads `f24ba6fa` (Tiny) and `cf50d5a4` (dense) add cookbook-only clarification; runtime file blobs remain unchanged.

One H200. Automatic pipeline configuration; server max running requests and graph batch 32. Dense MPS auto, Tiny MPS off. No CPU quota or affinity override. First 128 EN and 128 ZH samples of SeedTTS `27f4c1adee83b5b29b7c4b375f6b976324bda308`. All timed requests use reference audio/text conditioning. Per language/concurrency: nonstream42, stream42, stream43, nonstream43. Warmup equals concurrency. One service per model spans its 16 blocks; compilation and speaker caches persist. Dense prompt-latent caching is seed-keyed: stream42 can reuse nonstream42, while stream43 first introduces seed43. Tiny still encodes reference prompts in its engine. These are measurements of this replay protocol, not cold-reference latency or a cache-normalized A/B estimate.

Means are arithmetic seed means; p95s are seed ranges. First audio starts at request dispatch and ends at the first nonempty PCM packet. Playback begins immediately with no added buffer. Underrun is the maximum late playback deadline per request; fewer than two packets is N/A. Raw exported timing resolution is 0.1 ms.

These are mode comparisons within an integrated feature candidate, not isolated speedups against main. The latency subset is not full-corpus quality qualification.

## dense

### Non-streaming

| Split / concurrency | req/s | Completion mean / p95 (ms) | First audio mean / p95 (ms) | Failed / attempted |
| --- | ---: | --- | --- | --- |
| EN / 1 | 4.470 | 225.3 / 300.7–364.7 | N/A (completed WAV) | 0/256 |
| EN / 32 | 66.731 | 425.6 / 614.4–747.6 | N/A (completed WAV) | 0/256 |
| ZH / 1 | 3.245 | 308.6 / 369.4–409.2 | N/A (completed WAV) | 0/256 |
| ZH / 32 | 57.202 | 514.9 / 660.8–662.4 | N/A (completed WAV) | 0/256 |

### Streaming

| Split / concurrency | req/s | Completion mean / p95 (ms) | First audio mean / p95 (ms) | Failed / attempted |
| --- | ---: | --- | --- | --- |
| EN / 1 | 3.215 | 311.0 / 465.9–477.4 | 138.4 / 135.6–150.1 | 0/256 |
| EN / 32 | 17.102 | 1686.8 / 2155.1–2188.0 | 1241.6 / 1760.3–1783.2 | 0/256 |
| ZH / 1 | 2.269 | 440.4 / 530.7–539.3 | 138.8 / 136.2–151.2 | 0/256 |
| ZH / 32 | 13.221 | 2196.4 / 2720.9–2789.2 | 1442.2 / 2112.5–2184.1 | 0/256 |

| Split / concurrency | Max underrun per request: mean / p95 range (ms) | Requests with underrun / scored | N/A requests | c50 / c100 / c200 (%) |
| --- | --- | --- | ---: | --- |
| EN / 1 | 0.0 / 0.0–0.0 | 0/256 | 0 | 100.00 / 100.00 / 100.00 |
| EN / 32 | 0.0 / 0.0–0.0 | 0/256 | 0 | 100.00 / 100.00 / 100.00 |
| ZH / 1 | 0.0 / 0.0–0.0 | 0/256 | 0 | 100.00 / 100.00 / 100.00 |
| ZH / 32 | 0.0 / 0.0–0.0 | 0/256 | 0 | 100.00 / 100.00 / 100.00 |

HTTP smoke: complete; 14 raw PCM cases, plus SSE and disconnect recovery.

| Pair | Full / stream samples | Waveform correlation |
| --- | --- | --- |
| en-reference0 | 81144 / 81144 | 0.99970471 |
| en-reference1 | 109368 / 109368 | 0.97860435 |
| zh-reference0 | 172872 / 172872 | 0.99971071 |
| zh-reference1 | 285768 / 285768 | 0.99975406 |

## tiny

### Non-streaming

| Split / concurrency | req/s | Completion mean / p95 (ms) | First audio mean / p95 (ms) | Failed / attempted |
| --- | ---: | --- | --- | --- |
| EN / 1 | 0.917 | 1091.7 / 1691.8–1791.0 | N/A (completed WAV) | 0/256 |
| EN / 32 | 9.827 | 2920.7 / 5007.3–5527.3 | N/A (completed WAV) | 0/256 |
| ZH / 1 | 0.567 | 1765.6 / 2210.7–2319.0 | N/A (completed WAV) | 0/256 |
| ZH / 32 | 7.781 | 3839.3 / 5093.3–5129.4 | N/A (completed WAV) | 0/256 |

### Streaming

| Split / concurrency | req/s | Completion mean / p95 (ms) | First audio mean / p95 (ms) | Failed / attempted |
| --- | ---: | --- | --- | --- |
| EN / 1 | 0.861 | 1161.3 / 1872.8–1903.5 | 530.1 / 532.8–533.5 | 0/256 |
| EN / 32 | 7.484 | 3816.1 / 6877.7–7062.9 | 1610.2 / 2157.8–2389.3 | 0/256 |
| ZH / 1 | 0.518 | 1932.7 / 2423.4–2520.3 | 533.5 / 535.9–537.8 | 0/256 |
| ZH / 32 | 5.517 | 5353.8 / 7053.9–7134.6 | 1423.9 / 1829.2–1844.8 | 0/256 |

| Split / concurrency | Max underrun per request: mean / p95 range (ms) | Requests with underrun / scored | N/A requests | c50 / c100 / c200 (%) |
| --- | --- | --- | ---: | --- |
| EN / 1 | 0.0 / 0.0–0.0 | 0/253 | 3 | 100.00 / 100.00 / 100.00 |
| EN / 32 | 229.5 / 669.6–674.1 | 182/254 | 2 | 30.71 / 31.89 / 52.36 |
| ZH / 1 | 0.0 / 0.0–0.0 | 0/256 | 0 | 100.00 / 100.00 / 100.00 |
| ZH / 32 | 129.7 / 292.9–303.8 | 171/256 | 0 | 36.72 / 44.14 / 67.58 |

HTTP smoke: complete; 14 raw PCM cases, plus SSE and disconnect recovery.

| Pair | Full / stream samples | Waveform correlation |
| --- | --- | --- |
| en-reference0 | 882000 / 882000 | 0.99820813 |
| en-reference1 | 98784 / 98784 | 0.99949538 |
| zh-reference0 | 617400 / 617400 | 0.99862898 |
| zh-reference1 | 268128 / 268128 | 0.99955093 |

## Paired transcription check

Stage: complete. benchmarks.tasks.asr.normalize_text; ZH character based. This is a small functional comparison, not a full benchmark.

| Model / case | Full WER or CER | Stream WER or CER | Same normalized transcript |
| --- | ---: | ---: | --- |
| dense / en / reference=0 | 0.00% | 0.00% | True |
| dense / en / reference=1 | 0.00% | 0.00% | True |
| dense / zh / reference=0 | 4.55% | 4.55% | True |
| dense / zh / reference=1 | 4.55% | 4.55% | True |
| tiny / en / reference=0 | 0.00% | 0.00% | True |
| tiny / en / reference=1 | 0.00% | 0.00% | True |
| tiny / zh / reference=0 | 9.09% | 9.09% | True |
| tiny / zh / reference=1 | 4.55% | 4.55% | True |

## Validation and provenance

Integrated H200 Ming3/Ming-TTS suites: 227 passed. Prerequisite H200 Ming3/Ming-TTS suites: 211 passed. Tiny performance stack: 236 passed, 6 unsupported strided-normalization cases skipped. These counts do not include MPS or CPU-locality directories. Integrated all-file pre-commit passed. Initial test failures (missing import, missing argument, CPU fallback) were repaired before any benchmark block; no failed-source measurements were relabeled.

PRs: [3189](https://github.com/sgl-project/sglang-omni/pull/3189), [3190](https://github.com/sgl-project/sglang-omni/pull/3190); prerequisite [3136](https://github.com/sgl-project/sglang-omni/pull/3136). Historical PR descriptions are archived separately with their original model/source versions.

## Current non-streaming prerequisite

The [current-main prerequisite qualification](../ming3-nonstream-current-main/report.md) keeps complete paired cells, costs, source IDs and per-request evidence separate from these latency measurements. It also records the bitwise ASR WAV-preparation check for subsequent main commit `71bce692`.

## Final feature CI

Both final feature heads passed their unit-only workflows: [Tiny run40448255161](https://github.com/sgl-project/sglang-omni/actions/runs/40448255161), head `c864715c` tested at dependency merge `85322c03` (CPU A 4,729/87 skipped, CPU B 5,302/35, accelerator 1,127/28); [dense run40448260785](https://github.com/sgl-project/sglang-omni/actions/runs/40448260785), head `0ef18ce8` tested at dependency merge `999f365c` (CPU A 4,730/87, CPU B 5,302/35, accelerator 1,127/28). See `final-feature-ci.json` for exact revisions. These are dependency-branch checks, not final-main integration. The Ming3 graph/cache-dispatch accelerator test passed.
