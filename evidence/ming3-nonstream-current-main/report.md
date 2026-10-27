# Ming3 non-streaming current-main qualification

Audited arms: 64/92; updated 2026-10-27T16:48:38.886625+00:00. Only complete ABBA cells are aggregated.

Actual control `0fe60cf6c102caf982430e1764243c6e5c749d76`; candidate `3f8593f4cae19fe1c71e929a854bdc03b2c185e6`; corrected control `0d6a414e5e15c996900620d263143c89e0dd8acd`. `current-corrected-control.patch` reproduces that control from the actual main commit by retaining only the captured sampling-scale tensor. One H200, full SeedTTS EN/ZH, seeds42/43, A42/B42/B43/A43 per cell. Source receipts, exact commands/YAMLs, per-request results, per-sample SIM and WAV hashes are retained below `raw/`.

Protocol and metric definitions are in the original PR body and the archived release manifest. Each arm uses a fresh service and private compilation/reference caches; no CPU quota or affinity override. WER and CAM++ scores cover every request. Means are arithmetic seed means; p95 is the range of seed percentiles. The overview uses the geometric mean of matched EN/ZH throughput ratios. One-second GPU-memory sampling covers the TTS service window, excluding the later ASR scorer. The external graph observer is identical across arms.

Subsequent main `71bce692` wraps ASR WAV preparation with the existing audio loader. In this pinned image TorchCodec is available: eight real generated WAVs produced identical tensors and PCM16 bytes before and after that wrapper, with no CUDA context initialized by the probe. The fallback path is not exercised by these measurements. Actual benchmark source IDs above are retained; see `main71-decoder-equivalence.json` and its probe.

Subsequent main `e8050949` sets the FlashInfer architecture before stage processes launch. For the assigned H200/H100 (SM90), the pinned FlashInfer automatic target and explicit `9.0a` both resolve to `(9, "0a")`; SGLang already sets `9.0a`. This architecture-selection audit executes the installed class AST with mocked device capability, without importing Torch or launching CUDA work. It does not claim a new performance measurement on that main revision; see `main-e805-arch-equivalence.json` and its probe.

Later main changes through `a57209f8ac8ddff66c43e4c650310922114f522b` affect other-model/session paths, model registration, NPU router classification and the standalone GPU diagnostics CLI, with no identified Ming tensor-math edit. The registry eagerly imports models, so possible additional import-time startup overhead is not measured in these frozen-source cost rows. Source IDs and measurement dates are retained; final-main integration remains required. See `main-after-source-audit.json`.

## upstream

| Concurrency | EN/ZH geometric throughput change |
| --- | --- |
| 1 | +213.28% |
| 16 | +352.61% |
| 32 | +417.63% |
| 64 | +312.20% |

| Split | Concurrency | req/s A → B | Response mean / p95 range (ms), A → B | First packet | Mean audio seconds, A → B | WER (%), A → B | SIM, A → B | Failed / attempted, A → B |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| EN | 1 | 1.239 → 3.842 | 807.0 / 1085.0–1118.0 → 260.0 / 362.0–366.0 | N/A | 3.901 → 3.904 | 1.0090 → 0.9922 | 0.77661 → 0.77656 | 0/2176 → 0/2176 |
| EN | 16 | 8.925 → 41.895 | 1780.0 / 2673.0–2682.0 → 377.0 / 522.0–527.0 | N/A | 3.946 → 3.901 | 1.1304 → 1.0048 | 0.77886 → 0.77726 | 0/2176 → 0/2176 |
| EN | 32 | 11.630 → 61.270 | 2720.5 / 4111.0–4180.0 → 508.5 / 709.0–725.0 | N/A | 3.945 → 3.903 | 1.0173 → 0.9880 | 0.77855 → 0.77686 | 0/2176 → 0/2176 |
| EN | 64 | 13.440 → 56.835 | 4685.5 / 7554.0–7848.0 → 1107.5 / 1604.0–1669.0 | N/A | 3.957 → 3.904 | 1.0592 → 0.9797 | 0.77853 → 0.77693 | 0/2176 → 0/2176 |
| ZH | 1 | 0.978 → 3.093 | 1023.5 / 1295.0–1295.0 → 323.0 / 417.0–425.0 | N/A | 5.202 → 5.202 | 0.6447 → 0.6566 | 0.77992 → 0.78032 | 0/4040 → 0/4040 |
| ZH | 16 | 8.109 → 35.391 | 1967.5 / 2623.0–2651.0 → 449.5 / 573.0–582.0 | N/A | 5.261 → 5.202 | 0.7122 → 0.6589 | 0.78402 → 0.78018 | 0/4040 → 0/4040 |
| ZH | 32 | 11.106 → 56.487 | 2866.5 / 3831.0–3915.0 → 561.5 / 727.0–735.0 | N/A | 5.257 → 5.201 | 0.6802 → 0.6601 | 0.78347 → 0.78001 | 0/4040 → 0/4040 |
| ZH | 64 | 13.688 → 54.995 | 4630.5 / 6336.0–6432.0 → 1153.5 / 1504.0–1555.0 | N/A | 5.269 → 5.202 | 0.7015 → 0.6838 | 0.78361 → 0.78005 | 0/4040 → 0/4040 |

## lifetime-corrected

| Concurrency | EN/ZH geometric throughput change |
| --- | --- |
| 1 | +214.08% |
| 16 | +348.23% |
| 32 | +418.14% |
| 64 | +321.26% |

| Split | Concurrency | req/s A → B | Response mean / p95 range (ms), A → B | First packet | Mean audio seconds, A → B | WER (%), A → B | SIM, A → B | Failed / attempted, A → B |
| --- | ---: | --- | --- | --- | --- | --- | --- | --- |
| EN | 1 | 1.247 → 3.886 | 802.0 / 1090.0–1108.0 → 257.5 / 359.0–361.0 | N/A | 3.901 → 3.904 | 1.0131 → 0.9964 | 0.77661 → 0.77656 | 0/2176 → 0/2176 |
| EN | 16 | 9.011 → 41.906 | 1766.0 / 2561.0–2606.0 → 378.5 / 523.0–527.0 | N/A | 3.904 → 3.905 | 1.0006 → 1.0341 | 0.77653 → 0.77699 | 0/2176 → 0/2176 |
| EN | 32 | 11.832 → 63.200 | 2679.5 / 3968.0–4042.0 → 496.0 / 710.0–721.0 | N/A | 3.901 → 3.901 | 1.0090 → 1.0173 | 0.77657 → 0.77705 | 0/2176 → 0/2176 |
| EN | 64 | 13.612 → 59.563 | 4632.0 / 7199.0–7645.0 → 1054.5 / 1524.0–1534.0 | N/A | 3.902 → 3.904 | 0.9880 → 0.9420 | 0.77667 → 0.77744 | 0/2176 → 0/2176 |
| ZH | 1 | 0.980 → 3.101 | 1020.5 / 1293.0–1297.0 → 322.5 / 417.0–423.0 | N/A | 5.202 → 5.202 | 0.6364 → 0.6601 | 0.77992 → 0.78032 | 0/4040 → 0/4040 |
| ZH | 16 | 8.215 → 35.489 | 1943.0 / 2535.0–2550.0 → 448.0 / 567.0–592.0 | N/A | 5.201 → 5.201 | 0.6518 → 0.6589 | 0.78006 → 0.78012 | 0/4040 → 0/4040 |
| ZH | 32 | 11.208 → 56.334 | 2842.5 / 3760.0–3795.0 → 561.0 / 719.0–721.0 | N/A | 5.200 → 5.200 | 0.6613 → 0.6447 | 0.77986 → 0.78009 | 0/4040 → 0/4040 |
| ZH | 64 | 13.752 → 55.770 | 4620.5 / 6251.0–6386.0 → 1137.0 / 1478.0–1488.0 | N/A | 5.201 → 5.201 | 0.6495 → 0.6589 | 0.78003 → 0.78013 | 0/4040 → 0/4040 |

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
| upstream/en-c16 | 42 | -0.20933 | -0.0014849 |
| upstream/en-c16 | 43 | -0.04187 | -0.0016999 |
| upstream/en-c64 | 42 | -0.14234 | -0.0017516 |
| upstream/en-c64 | 43 | -0.01675 | -0.0014430 |
| upstream/zh-c1 | 42 | +0.02129 | +0.0001424 |
| upstream/zh-c1 | 43 | +0.00237 | +0.0006569 |
| upstream/zh-c16 | 42 | -0.06625 | -0.0039732 |
| upstream/zh-c16 | 43 | -0.04022 | -0.0037110 |
| upstream/zh-c32 | 42 | -0.04259 | -0.0033767 |
| upstream/zh-c32 | 43 | +0.00237 | -0.0035310 |
| upstream/zh-c64 | 42 | -0.06861 | -0.0038158 |
| upstream/zh-c64 | 43 | +0.03312 | -0.0033195 |
| lifetime-corrected/en-c32 | 42 | +0.01675 | +0.0002805 |
| lifetime-corrected/en-c1 | 43 | -0.03349 | -0.0003052 |
| lifetime-corrected/en-c16 | 42 | +0.01675 | +0.0008897 |
| lifetime-corrected/en-c16 | 43 | +0.05024 | +0.0000297 |
| lifetime-corrected/zh-c1 | 42 | +0.01893 | +0.0001424 |
| lifetime-corrected/zh-c1 | 43 | +0.02839 | +0.0006569 |
| lifetime-corrected/zh-c16 | 42 | +0.00946 | -0.0000283 |
| lifetime-corrected/zh-c16 | 43 | +0.00473 | +0.0001356 |
| lifetime-corrected/zh-c64 | 42 | +0.00473 | +0.0000861 |
| lifetime-corrected/zh-c64 | 43 | +0.01420 | +0.0001219 |

## Costs and output lengths

| Complete cell | Startup mean seconds, A → B | Peak sampled GiB, A → B | Captures, A → B | Output tokens, A → B |
| --- | --- | --- | --- | --- |
| upstream/en-c32 | 80.09 → 124.15 | 108.76 → 109.83 | [19] → [430] | 107287 → 106172 |
| upstream/en-c1 | 82.10 → 125.65 | 108.64 → 109.19 | [19] → [430] | 106087 → 106192 |
| upstream/en-c16 | 80.60 → 124.15 | 108.70 → 109.74 | [19] → [430] | 107354 → 106129 |
| upstream/en-c64 | 81.10 → 125.15 | 107.56 → 109.79 | [19] → [430] | 107632 → 106169 |
| upstream/zh-c1 | 79.60 → 125.66 | 108.66 → 109.19 | [19] → [430] | 262696 → 262704 |
| upstream/zh-c16 | 80.09 → 126.66 | 108.72 → 109.73 | [19] → [430] | 265706 → 262683 |
| upstream/zh-c32 | 82.10 → 123.14 | 108.77 → 108.92 | [19] → [430] | 265479 → 262665 |
| upstream/zh-c64 | 82.60 → 130.63 | 108.83 → 109.79 | [19] → [430] | 266102 → 262691 |
| lifetime-corrected/en-c32 | 80.09 → 128.14 | 107.54 → 108.98 | [19] → [430] | 106123 → 106100 |
| lifetime-corrected/en-c1 | 79.59 → 123.62 | 107.94 → 109.19 | [19] → [430] | 106087 → 106192 |
| lifetime-corrected/en-c16 | 85.62 → 123.14 | 108.69 → 109.73 | [19] → [430] | 106182 → 106211 |
| lifetime-corrected/en-c64 | 80.58 → 124.14 | 107.61 → 109.78 | [19] → [430] | 106147 → 106167 |
| lifetime-corrected/zh-c1 | 79.59 → 126.63 | 109.16 → 109.71 | [19] → [430] | 262696 → 262704 |
| lifetime-corrected/zh-c16 | 78.58 → 123.12 | 109.21 → 109.74 | [19] → [430] | 262674 → 262649 |
| lifetime-corrected/zh-c32 | 78.59 → 120.13 | 108.75 → 109.77 | [19] → [430] | 262591 → 262594 |
| lifetime-corrected/zh-c64 | 81.08 → 125.63 | 108.38 → 109.78 | [19] → [430] | 262647 → 262677 |

A is clean/corrected main for the first two comparisons, and native candidate for ablations. B is the candidate for the first two comparisons, and MPS off/cache off/fused flow off for the respective ablation. A partial matrix does not establish merge readiness.
