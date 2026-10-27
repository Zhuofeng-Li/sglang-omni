# Ming3 non-streaming current-main qualification

Audited arms: 8/92; updated 2026-10-27T05:05:31.594219+00:00. Only complete ABBA cells are aggregated.

Actual control `0fe60cf6c102caf982430e1764243c6e5c749d76`; candidate `3f8593f4cae19fe1c71e929a854bdc03b2c185e6`; corrected control `0d6a414e5e15c996900620d263143c89e0dd8acd`. One H200, full SeedTTS EN/ZH, seeds42/43, A42/B42/B43/A43 per cell. Source receipts, exact commands/YAMLs, per-request results, per-sample SIM and WAV hashes are retained below `raw/`.

Protocol and metric definitions are in the original PR body and the archived release manifest. Each arm uses a fresh service and private compilation/reference caches; no CPU quota or affinity override. WER and CAM++ scores cover every request. Means are arithmetic seed means; p95 is the range of seed percentiles. The overview uses the geometric mean of matched EN/ZH throughput ratios. One-second GPU-memory sampling covers the TTS service window, excluding the later ASR scorer. The external graph observer is identical across arms.

Subsequent main `71bce692` wraps ASR WAV preparation with the existing audio loader. In this pinned image TorchCodec is available: eight real generated WAVs produced identical tensors and PCM16 bytes before and after that wrapper, with no CUDA context initialized by the probe. The fallback path is not exercised by these measurements. Actual benchmark source IDs above are retained; see `main71-decoder-equivalence.json` and its probe.

Subsequent main `e8050949` sets the FlashInfer architecture before stage processes launch. For the assigned H200/H100 (SM90), the pinned FlashInfer automatic target and explicit `9.0a` both resolve to `(9, "0a")`; SGLang already sets `9.0a`. This architecture-selection audit executes the installed class AST with mocked device capability, without importing Torch or launching CUDA work. It does not claim a new performance measurement on that main revision; see `main-e805-arch-equivalence.json` and its probe.

## upstream

| Concurrency | EN/ZH geometric throughput change |
| --- | --- |
| 1 | Pending |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

| Split | Concurrency | req/s A → B | Response mean / p95 range (ms), A → B | First packet | Mean audio seconds, A → B | WER (%), A → B | SIM, A → B | Failed / attempted, A → B |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| EN | 1 | 1.239 → 3.842 | 807.0 / 1085.0–1118.0 → 260.0 / 362.0–366.0 | N/A | 3.901 → 3.904 | 1.0090 → 0.9922 | 0.77661 → 0.77656 | 0/2176 → 0/2176 |
| EN | 16 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |
| EN | 32 | 11.630 → 61.270 | 2720.5 / 4111.0–4180.0 → 508.5 / 709.0–725.0 | N/A | 3.945 → 3.903 | 1.0173 → 0.9880 | 0.77855 → 0.77686 | 0/2176 → 0/2176 |
| EN | 64 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |
| ZH | 1 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |
| ZH | 16 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |
| ZH | 32 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |
| ZH | 64 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |

## lifetime-corrected

| Concurrency | EN/ZH geometric throughput change |
| --- | --- |
| 1 | Pending |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

| Split | Concurrency | req/s A → B | Response mean / p95 range (ms), A → B | First packet | Mean audio seconds, A → B | WER (%), A → B | SIM, A → B | Failed / attempted, A → B |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| EN | 1 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |
| EN | 16 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |
| EN | 32 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |
| EN | 64 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |
| ZH | 1 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |
| ZH | 16 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |
| ZH | 32 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |
| ZH | 64 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |

## mps-attribution

| Concurrency | EN/ZH geometric throughput change |
| --- | --- |
| 1 | Pending |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

| Split | Concurrency | req/s A → B | Response mean / p95 range (ms), A → B | First packet | Mean audio seconds, A → B | WER (%), A → B | SIM, A → B | Failed / attempted, A → B |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| EN | 1 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |
| EN | 32 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |
| ZH | 1 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |
| ZH | 32 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |

## cache-attribution

| Concurrency | EN/ZH geometric throughput change |
| --- | --- |
| 1 | Pending |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

| Split | Concurrency | req/s A → B | Response mean / p95 range (ms), A → B | First packet | Mean audio seconds, A → B | WER (%), A → B | SIM, A → B | Failed / attempted, A → B |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| EN | 32 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |
| ZH | 32 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |

## fused-attribution

| Concurrency | EN/ZH geometric throughput change |
| --- | --- |
| 1 | Pending |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

| Split | Concurrency | req/s A → B | Response mean / p95 range (ms), A → B | First packet | Mean audio seconds, A → B | WER (%), A → B | SIM, A → B | Failed / attempted, A → B |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| EN | 32 | Pending | Pending | N/A | Pending | Pending | Pending | Pending |

## Per-seed adverse quality changes

| Cell | Seed | WER delta (percentage points) | SIM delta |
| --- | ---: | ---: | ---: |
| upstream/en-c32 | 42 | -0.05024 | -0.0014247 |
| upstream/en-c32 | 43 | -0.00837 | -0.0019417 |
| upstream/en-c1 | 42 | +0.00837 | +0.0002065 |
| upstream/en-c1 | 43 | -0.04187 | -0.0003052 |

## Costs and output lengths

| Complete cell | Startup mean seconds, A → B | Peak sampled GiB, A → B | Captures, A → B | Output tokens, A → B |
| --- | --- | --- | --- | --- |
| upstream/en-c32 | 80.09 → 124.15 | 108.76 → 109.83 | [19] → [430] | 107287 → 106172 |
| upstream/en-c1 | 82.10 → 125.65 | 108.64 → 109.19 | [19] → [430] | 106087 → 106192 |

A is clean/corrected main for the first two comparisons, and native candidate for ablations. B is the candidate for the first two comparisons, and MPS off/cache off/fused flow off for the respective ablation. A partial matrix does not establish merge readiness.
