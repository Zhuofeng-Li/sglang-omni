# Ming3 non-streaming current-main qualification

Audited arms: 4/92; updated 2026-10-27T03:59:43.790122+00:00. Only complete ABBA cells are aggregated.

Actual control `0fe60cf6c102caf982430e1764243c6e5c749d76`; candidate `3f8593f4cae19fe1c71e929a854bdc03b2c185e6`; corrected control `0d6a414e5e15c996900620d263143c89e0dd8acd`. One H200, full SeedTTS EN/ZH, seeds42/43, A42/B42/B43/A43 per cell. Source receipts, exact commands/YAMLs, per-request results, per-sample SIM and WAV hashes are retained below `raw/`.

Protocol and metric definitions are in the original PR body and the archived release manifest. Each arm uses a fresh service and private compilation/reference caches; no CPU quota or affinity override. WER and CAM++ scores cover every request. Means are arithmetic seed means; p95 is the range of seed percentiles. The overview uses the geometric mean of matched EN/ZH throughput ratios. One-second GPU-memory sampling covers the TTS service window, excluding the later ASR scorer. The external graph observer is identical across arms.

## upstream

| Concurrency | EN/ZH geometric throughput change |
| --- | --- |
| 1 | Pending |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

| Split | Concurrency | req/s A → B | Response mean / p95 range (ms), A → B | First packet | WER (%), A → B | SIM, A → B | Failed / attempted, A → B |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| EN | 1 | Pending | Pending | N/A | Pending | Pending | Pending |
| EN | 16 | Pending | Pending | N/A | Pending | Pending | Pending |
| EN | 32 | 11.630 → 61.270 | 2720.5 / 4111.0–4180.0 → 508.5 / 709.0–725.0 | N/A | 1.0173 → 0.9880 | 0.77855 → 0.77686 | 0/2176 → 0/2176 |
| EN | 64 | Pending | Pending | N/A | Pending | Pending | Pending |
| ZH | 1 | Pending | Pending | N/A | Pending | Pending | Pending |
| ZH | 16 | Pending | Pending | N/A | Pending | Pending | Pending |
| ZH | 32 | Pending | Pending | N/A | Pending | Pending | Pending |
| ZH | 64 | Pending | Pending | N/A | Pending | Pending | Pending |

## lifetime-corrected

| Concurrency | EN/ZH geometric throughput change |
| --- | --- |
| 1 | Pending |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

| Split | Concurrency | req/s A → B | Response mean / p95 range (ms), A → B | First packet | WER (%), A → B | SIM, A → B | Failed / attempted, A → B |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| EN | 1 | Pending | Pending | N/A | Pending | Pending | Pending |
| EN | 16 | Pending | Pending | N/A | Pending | Pending | Pending |
| EN | 32 | Pending | Pending | N/A | Pending | Pending | Pending |
| EN | 64 | Pending | Pending | N/A | Pending | Pending | Pending |
| ZH | 1 | Pending | Pending | N/A | Pending | Pending | Pending |
| ZH | 16 | Pending | Pending | N/A | Pending | Pending | Pending |
| ZH | 32 | Pending | Pending | N/A | Pending | Pending | Pending |
| ZH | 64 | Pending | Pending | N/A | Pending | Pending | Pending |

## mps-attribution

| Concurrency | EN/ZH geometric throughput change |
| --- | --- |
| 1 | Pending |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

| Split | Concurrency | req/s A → B | Response mean / p95 range (ms), A → B | First packet | WER (%), A → B | SIM, A → B | Failed / attempted, A → B |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| EN | 1 | Pending | Pending | N/A | Pending | Pending | Pending |
| EN | 32 | Pending | Pending | N/A | Pending | Pending | Pending |
| ZH | 1 | Pending | Pending | N/A | Pending | Pending | Pending |
| ZH | 32 | Pending | Pending | N/A | Pending | Pending | Pending |

## cache-attribution

| Concurrency | EN/ZH geometric throughput change |
| --- | --- |
| 1 | Pending |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

| Split | Concurrency | req/s A → B | Response mean / p95 range (ms), A → B | First packet | WER (%), A → B | SIM, A → B | Failed / attempted, A → B |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| EN | 32 | Pending | Pending | N/A | Pending | Pending | Pending |
| ZH | 32 | Pending | Pending | N/A | Pending | Pending | Pending |

## fused-attribution

| Concurrency | EN/ZH geometric throughput change |
| --- | --- |
| 1 | Pending |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

| Split | Concurrency | req/s A → B | Response mean / p95 range (ms), A → B | First packet | WER (%), A → B | SIM, A → B | Failed / attempted, A → B |
| --- | ---: | --- | --- | --- | --- | --- | --- |
| EN | 32 | Pending | Pending | N/A | Pending | Pending | Pending |

## Per-seed adverse quality changes

| Cell | Seed | WER delta (percentage points) | SIM delta |
| --- | ---: | ---: | ---: |
| upstream/en-c32 | 42 | -0.05024 | -0.0014247 |
| upstream/en-c32 | 43 | -0.00837 | -0.0019417 |

## Costs and output lengths

| Complete cell | Startup mean seconds, A → B | Peak sampled GiB, A → B | Captures, A → B | Output tokens, A → B |
| --- | --- | --- | --- | --- |
| upstream/en-c32 | 80.09 → 124.15 | 108.76 → 109.83 | [19] → [430] | 107287 → 106172 |

A is clean/corrected main for the first two comparisons, and native candidate for ablations. B is the candidate for the first two comparisons, and MPS off/cache off/fused flow off for the respective ablation. A partial matrix does not establish merge readiness.
