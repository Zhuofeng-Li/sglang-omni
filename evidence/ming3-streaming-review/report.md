# Ming3 streaming review evidence

Measurement blocks: **16/32**. **In progress; partial results are not a full qualification.**

Measured integration: `251f02b467fe06269cb2d3d8c1063565d7c3de82`, tree `3e68505e3a2c26ae6e88e8360007bc0d3896d5d7`. The final dense head `8ca2534388574830fbfb3b692feee6851c57e0f2` has the identical tree. Tiny head `5c955911` differs only in the companion dense enablement guard and its test.

One H200. Automatic pipeline configuration; server max running requests and graph batch 32. Dense MPS auto, Tiny MPS off. No CPU quota or affinity override. First 128 EN and 128 ZH samples of SeedTTS `27f4c1adee83b5b29b7c4b375f6b976324bda308`. Per language/concurrency: nonstream42, stream42, stream43, nonstream43. Warmup equals concurrency. One service per model spans its 16 blocks; reference and compilation caches persist across blocks.

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
| EN / 1 | Pending | Pending | Pending | Pending |
| EN / 32 | Pending | Pending | Pending | Pending |
| ZH / 1 | Pending | Pending | Pending | Pending |
| ZH / 32 | Pending | Pending | Pending | Pending |

### Streaming

| Split / concurrency | req/s | Completion mean / p95 (ms) | First audio mean / p95 (ms) | Failed / attempted |
| --- | ---: | --- | --- | --- |
| EN / 1 | Pending | Pending | Pending | Pending |
| EN / 32 | Pending | Pending | Pending | Pending |
| ZH / 1 | Pending | Pending | Pending | Pending |
| ZH / 32 | Pending | Pending | Pending | Pending |

| Split / concurrency | Max underrun per request: mean / p95 range (ms) | Requests with underrun / scored | N/A requests | c50 / c100 / c200 (%) |
| --- | --- | --- | ---: | --- |
| EN / 1 | Pending | Pending | Pending | Pending |
| EN / 32 | Pending | Pending | Pending | Pending |
| ZH / 1 | Pending | Pending | Pending | Pending |
| ZH / 32 | Pending | Pending | Pending | Pending |

HTTP smoke: None; 0 raw PCM cases, plus SSE and disconnect recovery.

| Pair | Full / stream samples | Waveform correlation |
| --- | --- | --- |

## Paired transcription check

Pending after all latency measurements, to avoid GPU interference.

## Validation and provenance

Integrated H200 Ming3/Ming-TTS suites: 227 passed. Prerequisite H200 Ming3/Ming-TTS suites: 211 passed. Tiny performance stack: 236 passed, 6 unsupported strided-normalization cases skipped. These counts do not include MPS or CPU-locality directories. Integrated all-file pre-commit passed. Initial test failures (missing import, missing argument, CPU fallback) were repaired before any benchmark block; no failed-source measurements were relabeled.

PRs: [3189](https://github.com/sgl-project/sglang-omni/pull/3189), [3190](https://github.com/sgl-project/sglang-omni/pull/3190); prerequisite [3136](https://github.com/sgl-project/sglang-omni/pull/3136). Historical PR descriptions are archived separately with their original model/source versions.
