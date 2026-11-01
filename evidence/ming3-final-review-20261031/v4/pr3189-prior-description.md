## Changes

Enable opt-in streaming audio for Ming3 Tiny. Dependency order is **#3136 → #3189 → #3190**. The two feature PRs remain linked in native stack #3254; merge only the validated prefix #3136 → #3189 → #3190 through the native stack workflow, preserving dependency order. Draft #3217 is outside this qualification and must remain unmerged. Do not merge a feature into its temporary dependency branch.

- Extract the existing Ming-Omni-TTS batched AudioVAE decoder and streaming scheduler into `sglang_omni/modules/ming_audio/`; both model adapters reuse it. Keep the old Ming-TTS imports compatible.
- Batch active requests into fixed incremental cache slots, with cancellation and late-chunk cleanup. Preserve terminal `finish_reason`, usage and the final tail.
- Preserve #3136's full vocoder CUDA-graph path for `stream=false`; `stream=true` uses incremental attention/interpolation/ISTFT state. CPU non-streaming keeps its full decoder fallback.

- Preserve full-response CPU vocoder fallback for `stream=true`: derive the engine routing from the selected vocoder, keep complete terminal latents and omit unused incremental chunks for the CPU scheduler. Tiny CUDA incremental decoding is retained. At this intermediate head, dense 0.5B `stream=true` keeps the complete-response fallback (`enable_dense_streaming=False`) instead of rejecting the request; #3190 enables dense incremental output.

**Changed defaults**

The intermediate dense incremental switch defaults off; dense streaming requests remain accepted through full-response decoding.

Streaming remains opt-in (`stream=true`, `response_format=pcm`). The default chunk is eight latent steps, with a fixed cache capacity of 32. The first non-empty packet needs latent 17; shorter utterances flush at completion. Eight steps is a decoder grouping parameter, not an elapsed-time latency promise. Non-streaming deployment and graph defaults come from #3136.

Both checkpoint families inherit shared **MPS off** from #3136; explicit `--mps auto` remains available.

## Paired comparison on current main

<!-- final-integration-review-20261031 -->
Head `35bf42ec695da774d6e1cf8731c70b291d671af9`; frozen actual main `74003d00f53e7f1a05593b556f21a31760a6fab6`. Main #3355 is integrated. Later main `3cb3c6ccb6ca9aa40dc5fa58773d6e773c2b9189` only changes Ming-ASR encoder paths, audited separately from this Ming3-TTS/Qwen3-ASR evaluation. Only #3136 → #3189 → #3190 is included; draft #3217 is excluded. Individual diffs contain no doc/docs changes.

The maintainer-requested **default MPS-off** paired measurements are complete: frozen main `74003d00f53e7f1a05593b556f21a31760a6fab6` → measured #3136 `78d8c310a65c14dd4bceb87e220c8304917805bb`, full EN c16 and ZH c1 corpora, seeds42/43 in ABBA order. Final #3190 `2a636231d688b7bc83d78769e4f5162502680675` receives a separate same-source non-streaming → streaming comparison with full-corpus WER/SIM/failure coverage and two-seed ABBA: **EN c16 and ZH c1 are complete**. This integrated mode comparison is not an independent #3189 performance claim. The clean-main ZH A42 control was reused with its original raw configuration/source identity, unchanged native MPS-off setting, image, model/data pins and device; the fresh EN default-off ABBA has also completed. Earlier MPS-enabled results remain separate. Later publication heads remove only the redundant test file; runtime/model/evaluator/config sources match the recorded measurement identities. Required approvals and final merged-main overall validation remain pending.

One dedicated H200; PyTorch 2.14.1, SGLang 0.5.22, Transformers 5.19.0, FlashInfer 0.7.1. Ming0.5B revision `8d66b70a00f05ad183fa8a863b4ce609fc83cbc0`; SeedTTS Arrow `27f4c1adee83b5b29b7c4b375f6b976324bda308`, full EN 1088/ZH 2020 per arm. Common launch settings: max running requests 64, graph batch 64, output tokens 2048; warmup equals client concurrency. Every arm saves its YAML, resolved defaults and private cold compilation/reference caches. Qwen3-ASR scores WER; pinned CAM++ scores SIM. No quality non-inferiority margin was predeclared.
<!-- final-integration-review-20261031-end -->

### Non-streaming

| Concurrency | EN/ZH geometric throughput change |
| --- | --- |
| 1 | Pending |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

Only EN c16 and ZH c1 were requested for this refresh; cross-language geometric means require matching concurrency and cannot combine these two cells. Other matrix cells remain historical in the evidence.

| Default-off comparison | req/s | Response mean / p95 (ms) | First packet | WER (%) | SIM | Failures |
| --- | --- | --- | --- | --- | --- | --- |
| Main → #3136, EN c16 | 9.017 → 35.854 (+297.63%) | 1765.5 / 2582–2642 → 443.5 / 606–636 | N/A | 1.088504 → 1.008959 | 0.778928 → 0.776780 | 0/2176 → 0/2176 |
| Main → #3136, ZH c1 | 0.969 → 3.457 (+256.71%) | 1032.0 / 1292–1330 → 289.0 / 377–381 | N/A | 0.644726 → 0.657739 | 0.779919 → 0.780319 | 0/4040 → 0/4040 |

<!-- default-off-complete-blocks-20261031 -->
**EN c16, default MPS off, complete two-seed ABBA:** arithmetic seed means; p95 is the seed range. WER changes -0.079545 percentage points (seed42 -20 edits; seed43 +1 edits); SIM changes -0.002148. Mean output audio 3.948199 → 3.902500 s. Output tokens by seed42/43: 54086/53305 → 53407/52741. Finish reasons observed: 0/2176 → 2176/2176; unknown main reasons do not prove absence of truncation. Raw-main comparisons include the sampling-storage lifetime correction; no quality non-inferiority margin or pure-optimization attribution is assumed.

**ZH c1, default MPS off, complete two-seed ABBA:** arithmetic seed means; p95 is the seed range. WER changes +0.013013 percentage points (seed42 +5 edits; seed43 +6 edits); SIM changes +0.000400. Mean output audio 5.201901 → 5.202059 s. Output tokens by seed42/43: 131679/131017 → 131772/130932. Finish reasons observed: 0/4040 → 4040/4040; unknown main reasons do not prove absence of truncation. Raw-main comparisons include the sampling-storage lifetime correction; no quality non-inferiority margin or pure-optimization attribution is assumed.
<!-- default-off-complete-blocks-20261031-end -->

### Streaming

| Concurrency | EN/ZH geometric throughput change |
| --- | --- |
| 1 | Pending |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

Streaming is opt-in. Clean main has no equivalent incremental endpoint; final-head non-streaming/streaming mode comparisons establish quality and latency behavior, not an independent main-to-PR speedup.

| Final #3190 non-streaming → streaming | req/s | Response mean / p95 range (ms) | First packet mean / p95 range | WER | SIM | Failures |
| --- | --- | --- | --- | --- | --- | --- |
| EN c16 | 35.675 → 15.001 (-57.95%) | 445.5 / 613.0–631.0 → 1061.5 / 1333.0–1337.0 | N/A → 659.1 / 759.0–772.4 ms | 0.996400 → 0.988026% | 0.776854 → 0.780522 | 0/2176 → 0/2176 |
| ZH c1 | 3.451 → 2.175 (-36.99%) | 289.5 / 377.0–378.0 → 460.0 / 594.0–594.0 | N/A → 155.5 / 191.3–193.6 ms | 0.661288 → 0.657739% | 0.780319 → 0.780663 | 0/4040 → 0/4040 |

<!-- final-mode-complete-blocks -->
Same-source mode comparison on measured `2a636231d688b7bc83d78769e4f5162502680675`; two full-corpus seeds42/43 in A42/B42/B43/A43 order. Means are seed arithmetic means; p95 values are seed ranges. This estimates mode costs on the final source, separately from main→PR gains. **EN c16, complete ABBA:** WER -0.008373 percentage points (seed42 120→113 edits; seed43 118→123 edits); SIM +0.003669. Audio mean 3.904485→3.903309s (-0.030131%); output tokens seed42/43 53465/52737→53419/52751. All 2176 stream requests have valid positive first packets; both modes report stop for every request and zero reported length finishes. Streaming throughput and response latency costs, including first-packet delay relative to nonstreaming complete responses, are retained. No quality noninferiority margin was predeclared.

**ZH c1, complete ABBA:** WER -0.003549 percentage points (seed42 274→268 edits; seed43 285→288 edits); SIM +0.000344. Audio mean 5.202059→5.202059s (+0.000000%); output tokens seed42/43 131772/130932→131772/130932. All 4040 stream requests have valid positive first packets; both modes report stop for every request and zero reported length finishes. Streaming throughput and response latency costs, including first-packet delay relative to nonstreaming complete responses, are retained. No quality noninferiority margin was predeclared.
<!-- /final-mode-complete-blocks -->

<!-- historical-tiny-load-limit -->
**Historical Tiny mode timing, retained for the original review request:** one H200 at measured integration `251f02b467fe06269cb2d3d8c1063565d7c3de82`, Tiny runtime `5c955911`; first128 EN/ZH samples, seeds42/43 in nonstream42/stream42/stream43/nonstream43 order, Tiny MPS off, warm service/caches, server limit32. Means are seed arithmetic means; p95 values are seed ranges. These older-source observations are not relabeled as current-head, independent main→#3189 gains or full-corpus Tiny quality qualification.

| Tiny split / concurrency | req/s nonstream→stream | Completion mean / p95 ms nonstream→stream | Stream first audio mean / p95 ms | Max playback underrun mean / p95 ms | Underrun/scored (N/A) | Failures nonstream→stream |
| --- | --- | --- | --- | --- | --- | --- |
| EN / 1 | 0.917→0.861 | 1091.7 / 1691.8–1791.0→1161.3 / 1872.8–1903.5 | 530.1 / 532.8–533.5 | 0.0 / 0.0–0.0 | 0/253 (3) | 0/256→0/256 |
| EN / 32 | 9.827→7.484 | 2920.7 / 5007.3–5527.3→3816.1 / 6877.7–7062.9 | 1610.2 / 2157.8–2389.3 | 229.5 / 669.6–674.1 | 182/254 (2) | 0/256→0/256 |
| ZH / 1 | 0.567→0.518 | 1765.6 / 2210.7–2319.0→1932.7 / 2423.4–2520.3 | 533.5 / 535.9–537.8 | 0.0 / 0.0–0.0 | 0/256 (0) | 0/256→0/256 |
| ZH / 32 | 7.781→5.517 | 3839.3 / 5093.3–5129.4→5353.8 / 7053.9–7134.6 | 1423.9 / 1829.2–1844.8 | 129.7 / 292.9–303.8 | 171/256 (0) | 0/256→0/256 |

Playback starts immediately without added buffering; fewer than two packets is N/A, not zero underrun. The real c32 underruns remain an explicit load limit. This timing subset has no corpus-level Tiny WER/SIM or cold-start/memory/capture-delta qualification; the Dense corpus results do not supply it. Full raw timing, functional/paired-ASR scope and source history remain in the single linked evidence record. No smaller-first-group ablation or new experiment is claimed.
<!-- /historical-tiny-load-limit -->

**Optional MPS-enabled historical comparison (not default-off results).** On 2026-10-31, main `74003d00` with MPS off → #3136 `b6d7dbc5` with MPS auto, full EN c16 ABBA: mean req/s **8.863 → 41.617 (+369.56%)**, response mean **1795.5 → 380.5 ms**, seed p95 range **2675–2690 → 526–526 ms**, WER **1.075944% → 0.996400%**, SIM **0.778832 → 0.776681**, failures **0/2176 → 0/2176**. Mean output audio **3.945993 → 3.903199 s**. This compares the whole candidate with optional MPS, not an isolated MPS benefit; quality includes the sampling-storage correctness fix and SIM decreases by 0.002150. No non-inferiority claim. Previous broad matrices, lifetime-corrected controls, ablations and original source IDs remain in the single linked evidence record.

## Costs

<!-- vocoder-graph-setup-component -->
**Vocoder graph setup component (measured #3136 `78d8c310`, default MPS off):** the384-graph setup phase logs EN c16 seed42/43 **34.425/34.115s** (mean **34.270s**) and ZH c1 **49.810/37.612s** (mean **43.711s**). Every arm logs **5,505,024 bytes (5.25MiB)** of shared input/output backing storage. This excludes graph-pool/model memory; use the observed device-peak table for the whole service. Warmups/captures are included in this phase, while other stages initialize concurrently, so it is not an additive allocation of total cold-start delta. Current CPU/CUDA bit-for-bit decoder tests pass; full per-seed logs and source proof are in the linked evidence.
<!-- /vocoder-graph-setup-component -->

| Default-off condition | Startup mean (s), main → PR (delta) | Observed peak GiB, main → PR (delta) | Successful capture events/arm (delta) |
| --- | --- | --- | --- |
| EN c16 | 96.096 → 130.143 (+34.048) | 108.6943 → 109.6221 (+0.9277) | 19 → 430 (+411) |
| ZH c1 | 93.605 → 143.174 (+49.569) | 107.4209 → 109.1416 (+1.7207) | 19 → 430 (+411) |

<!-- final-mode-costs -->
| Final-head mode cost, nonstream → stream | Startup mean s (delta) | Observed peak GiB (delta) | Successful capture events/arm (delta) |
| --- | --- | --- | --- |
| EN c16 | 137.170 → 140.674 (+3.504) | 108.8389 → 110.0674 (+1.2285) | 430 → 430 (+0) |
| ZH c1 | 152.698 → 136.177 (-16.521) | 108.3447 → 108.7490 (+0.4043) | 430 → 430 (+0) |
<!-- /final-mode-costs -->

For the historical optional-MPS EN c16 block only: mean startup **94.1145 → 137.1715 s (+43.057 s)**; observed peak TTS device memory across seeds **108.6943 → 109.6670 GiB**; successful capture events **19 → 430** per seed. Capture events are not guaranteed unique resident graphs. Memory sampling is nominally 1 s with raw gaps retained, not an instantaneous peak guarantee. The same external observer applies to both arms. Caches and captured graph storage add memory/startup costs; no default-off costs are inferred from these optional-on rows.

## Tests

<!-- current-complete-ci -->
- Full `pre-commit run --all-files` passed on the #3136 and final integrated publication sources. Retained regressions cover legacy factory import/arguments, Tiny/Dense checkpoint defaults and round-trip, CPU vocoder fallback, graph/lifetime correctness and explicit overrides. The redundant MPS-default test file was removed in response to review; runtime/model/evaluator/config files are byte-identical to the recorded benchmark sources. The earlier pinned-runtime run passed416 cases with zero skips before that12-case duplicate-file removal;24 resolved-config equivalence cases passed. Historical checks stay attributed to their original revisions in the evidence record.
- Publication head `75500328388a30af3a0a91e1190b36b178bf08f5`: [selected Omni CI](https://github.com/sgl-project/sglang-omni/actions/runs/41246664995) **completed successfully**. Gate/preflight/setup passed; selection was PR Test only (`run-unit-test-ci-only`). All four unit jobs used synthetic checkout `bebb17690054d4069e1cbfbbc91ab579770ba962`, tree `7c059be2376934e183aebf4f4ccd7ac2dc907d79`, incorporating main e727710a. Observed main at this update: `e727710aa6a0b29cef7dc362155c350dae313f21`. Corpus measurements retain their stated frozen source identities; final merged-main overall validation remains pending.

| Current unit partition | Passed | Skipped |
| --- | ---: | ---: |
| A | 3267 | 36 |
| B | 3813 | 28 |
| C | 3605 | 62 |
| Accelerator | 1214 | 31 |

All four unit partitions passed on their first attempts.

Skipped/deselected cases are not passes. ASR/TTS/Omni stages were unselected; MPS was also unselected for the companions. Independent ephemeral-home cleanup is workflow_dispatch-only and skipped here, not a cleanup pass. All16 scoped corpus arms completed and were verified; review requests, required approvals and final merged-main overall validation remain separate gates. No merge-readiness claim.
<!-- /current-complete-ci -->

Developed through [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) in [OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index), with co-author [Ethan Feng](https://yichenfeng.me/); [validation and complete historical evidence](https://github.com/Zhuofeng-Li/sglang-omni/blob/codex/ming3-streaming-review-evidence/evidence/ming3-final-review-20261031/v3/report.md).
