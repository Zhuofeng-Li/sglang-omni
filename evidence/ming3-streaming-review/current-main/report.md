# Current-main Ming3 streaming validation

Latest cookbook-only heads: Tiny `c864715c`, dense `0ef18ce8`. The cookbook now explicitly requires `response_format="pcm"` with `stream=true`; runtime files match the metadata-only predecessors.

Subsequent metadata-only heads are Tiny `6dc90443` and dense `17aba451`. They change only the static streaming capability declaration used by the startup log. The 20 CPU model-capability tests and both architecture aliases pass; measured synthesis/scheduler/tensor paths remain unchanged. All timing and HTTP records retain their original measured commits.

Base: `0fe60cf6c102caf982430e1764243c6e5c749d76`; measured integration: `348f6973d4878ed77a9c6c60d072c91addaf15d8`.

This is a fresh 0.5B mode comparison on the merged current-main implementation, not an isolated speedup over main. The original Tiny timing data in the parent report retain their original source and date. Tiny preprocessing remains concurrency one and does not use the changed bounded worker pool; both models received fresh HTTP and paired transcription checks here.

Protocol matches the parent report: one H200, automatic config, 128 EN/ZH reference-conditioned requests, seeds 42/43, nonstream42 → stream42 → stream43 → nonstream43 per cell, c1/c32, server limits 32, native warmup equal to concurrency. One service spans all 16 dense blocks. Dense reference cache is seed-keyed and persists; stream42 can reuse nonstream42 while stream43 first introduces seed43. This is neither cold-reference latency nor a cache-normalized performance gain. Means are arithmetic seed means; p95 is the range of the two seed values.

### Non-streaming

| Split / concurrency | req/s | Completion mean / p95 (ms) | First audio mean / p95 (ms) | Failed / attempted |
| --- | ---: | --- | --- | --- |
| EN / 1 | 4.489 | 224.3 / 304.1–375.9 | N/A (completed WAV) | 0/256 |
| EN / 32 | 66.413 | 428.2 / 647.5–737.1 | N/A (completed WAV) | 0/256 |
| ZH / 1 | 3.238 | 309.3 / 365.7–412.5 | N/A (completed WAV) | 0/256 |
| ZH / 32 | 56.028 | 528.3 / 662.0–764.9 | N/A (completed WAV) | 0/256 |

### Streaming

| Split / concurrency | req/s | Completion mean / p95 (ms) | First audio mean / p95 (ms) | Failed / attempted |
| --- | ---: | --- | --- | --- |
| EN / 1 | 3.186 | 313.7 / 475.4–479.4 | 139.2 / 135.1–155.7 | 0/256 |
| EN / 32 | 17.388 | 1657.3 / 2154.8–2156.0 | 1204.8 / 1698.1–1717.6 | 0/256 |
| ZH / 1 | 2.263 | 441.8 / 532.5–538.4 | 138.1 / 137.1–151.3 | 0/256 |
| ZH / 32 | 13.724 | 2119.2 / 2597.8–2652.2 | 1367.2 / 1978.4–2062.8 | 0/256 |

| Split / concurrency | Max underrun per request: mean / p95 range (ms) | Requests with underrun / scored | N/A requests | c50 / c100 / c200 (%) |
| --- | --- | --- | ---: | --- |
| EN / 1 | 0.0 / 0.0–0.0 | 0/256 | 0 | 100.00 / 100.00 / 100.00 |
| EN / 32 | 0.0 / 0.0–0.0 | 0/256 | 0 | 100.00 / 100.00 / 100.00 |
| ZH / 1 | 0.0 / 0.0–0.0 | 0/256 | 0 | 100.00 / 100.00 / 100.00 |
| ZH / 32 | 0.0 / 0.0–0.0 | 0/256 | 0 | 100.00 / 100.00 / 100.00 |

Playback begins immediately at the first nonempty packet, without added buffering. Underrun is the maximum late playback deadline per request; one-packet responses are N/A and excluded. Raw exported time resolution is 0.1 ms.

### Functional checks

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

Each model passed 14 PCM cases plus SSE and disconnect recovery. Matching ASR transcripts are a small functional check, not full-corpus quality qualification.

Pinned H200 test suites, including Ming3/Ming-TTS, MPS, CPU-locality, shared scheduler and stage environment: candidate `3f8593f` 386 passed; integrated stream `348f697` 402 passed; Tiny performance `ea0958c` 411 passed and 6 skipped. Full logs and source receipts are under `raw/`.
