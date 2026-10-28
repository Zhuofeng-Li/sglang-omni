# Ming review follow-up — 2026-10-28

Status: current-head code/CI and the requested quality follow-up are complete; quality acceptance and required reviews remain pending. This report does not qualify #3217 for release.

## Source and correctness

Original PR heads: #3136 `02103f988e5fc5d50e507318f66dbcdeb879931d`, #3189 `e2d7a33a63d8dba2d3410dea82677909e974b8c5`, #3190 `d57f2e970df64266b04e09bf716ba0ecc2342eca`, #3217 `96957d08e9dcd260005f5e92b9d13e90c544bbcf`. Integration base is main `61a23967f010de309e65e6f1b1c3819be4b51e86`. Later main `c7b09e42` changes documentation tooling and Qwen3-TTS only; frozen paired blocks are retained.

The shared decoder preserves main's Triton BTH upsample implementation at its common-module path, with compatibility exports at the old Ming-TTS import path. The new upsample test imports the defining shared decoder module; assertions are unchanged. Cumulative candidate tree `a41d246dc14e476e4aaff18088e99cba76910fd7` passed 276 Ming3/Ming-TTS tests, 6 skipped, on H200. Full pre-commit passed. The final attribution-only commit has identical Python ASTs to parent `a1c337c0` in all three affected files and names Zhuofeng Li in all five new notes.

## Current CI

The four linked records verify actual test checkout SHAs, parentage, pass/skip counts and unit post-job cleanup. Runs: #3136 [40749897047](https://github.com/sgl-project/sglang-omni/actions/runs/40749897047), #3189 [40749898756](https://github.com/sgl-project/sglang-omni/actions/runs/40749898756), #3190 [40749899471](https://github.com/sgl-project/sglang-omni/actions/runs/40749899471), #3217 [40750866735](https://github.com/sgl-project/sglang-omni/actions/runs/40750866735), all successful. #3217 is manual unit-only dispatch while Draft; its automatic Draft gate is expected and is not a passing check. No checks or protection were bypassed.

#3136 additionally passed the actual MPS/Higgs preset on exact head02103f98. Saved artifact12846337026 confirms1088 canonical requests,8 overlap-canary requests, quality guards and full process/port/MPS cleanup. This is cross-model lifecycle coverage, not Ming target-model validation. There is no Ming3/Ming-Omni-TTS preset; other model presets are not substitutes.

## #3136 requested quality follow-up

**Complete:** 12 arms / 18,648 formal requests, zero failures. Full EN 1,088 and ZH 2,020 per arm. Per cell the order is A42,B42,B43,A43,repeat-A42,repeat-A43 on one H200 `GPU-99e2ecd1-862a-4af1-222d-841708198f30`. Historical corrected-control source `0d6a414e5e15c996900620d263143c89e0dd8acd` and candidate `3f8593f4cae19fe1c71e929a854bdc03b2c185e6` were frozen throughout. These are review-requested source reproductions, not speedup measurements on today’s main. A read-only Hugging Face cache preflight failed before formal requests; the assets mount was made writable for normal snapshot bookkeeping, with the same mount/runtime policy in every accepted arm. Its failure evidence was retained separately.

Model `inclusionAI/Ming-3.0-tts-0.5B@8d66b70a00f05ad183fa8a863b4ce609fc83cbc0`; data `zhaochenyang20/seed-tts-eval-arrow@27f4c1adee83b5b29b7c4b375f6b976324bda308`; scorer `Qwen/Qwen3-ASR-1.7B@7278e1e70fe206f11671096ffdd38061171dd6e5`; fixed CAM++. Original operator/evaluator and full-split request order retained, per-request seed42/43, nonstream, max-running/graph64, fresh service/cache per arm, native default CPU scheduling. All fresh arms share the same runtime. [Recorded historical/fresh runtime comparison](historical-fresh-runtime-comparison.json) discloses the Torch distribution strings2.14.1 versus2.14.1+cu130; no binary-identical runtime claim. The legacy CSV column `whisper_text` contains Qwen ASR output.

| Split/c | Seed | Historical A/B edits | Fresh A/B edits | Fresh Δ WER (pp) | Repeated A edits | Repeat Δ WER (pp) | Fresh SIM A → B |
|---|---:|---:|---:|---:|---:|---:|---:|
| EN c16 | 42 | 120/122 | 121/117 | -0.033492 | 121 | +0.000000 | 0.775895 → 0.776506 |
| EN c16 | 43 | 119/125 | 121/124 | +0.025119 | 122 | +0.008373 | 0.777017 → 0.777732 |
| ZH c1 | 42 | 264/272 | 266/271 | +0.011830 | 264 | -0.004732 | 0.780467 → 0.780610 |
| ZH c1 | 43 | 274/286 | 282/286 | +0.009464 | 285 | +0.007098 | 0.779372 → 0.780029 |

Denominators are 11,943 EN reference units and 42,266 ZH reference units. Original corrected-control positive WER deltas are preserved, not overwritten. Fresh EN signs differ between seeds; fresh ZH positive deltas remain visible. Repeated controls and exactly identical WAVs with different transcriptions demonstrate scorer variability, not non-inferiority or a proof that every quality difference is evaluator noise.

| Comparison | Same WAVs | Same-WAV changed ASR transcripts | Net edit change |
|---|---:|---:|---:|
| EN A42 → repeat-A42 | 1039/1088 | 5 | +0 |
| EN A43 → repeat-A43 | 1048/1088 | 12 | +1 |
| ZH A42 → repeat-A42 | 2020/2020 | 16 | -2 |
| ZH A43 → repeat-A43 | 2020/2020 | 18 | +3 |
| ZH historical-A42 → fresh-A42 | 2020/2020 | 16 | +2 |
| ZH historical-B42 → fresh-B42 | 2020/2020 | 21 | -1 |
| ZH historical-B43 → fresh-B43 | 2020/2020 | 16 | +0 |
| ZH historical-A43 → fresh-A43 | 2020/2020 | 19 | +8 |

[Original affected transcript inspection](paired-error-inspection.json) includes segmentation (moon bounce/moonbounce), number rendering (二零零九/2009), homophones and lexical changes. [Fresh paired and same-control transcript differences](quality-repeat-analysis.json) retain all examples. [Selected affected recordings](audio-examples.md) ([hash index](quality-audio-index.json)) explicitly identify exact historical waveform reconstructions; fresh EN recordings are not mislabeled as old files. No claim of listening to original unavailable recordings is made.

The reviewer is asked to assess these measured quality differences; no formal equivalence margin was specified or inferred. Current CI/correctness checks are separately reported above. Original 92-arm throughput/ablation qualification retains its actual dates/revisions and remains linked in Prior complete records.

## #3217 requested shared-model validation

**Complete bounded shared-model check:** 32 arms / 1,024 formal requests, zero failures or output-budget hits. First 32 EN and ZH SeedTTS samples; c1/c8; both modes; startup seeds 42/43 ABBA. Control is #3190 `d57f2e970df64266b04e09bf716ba0ecc2342eca` (tree64a386f4); candidate is #3217 `96957d08e9dcd260005f5e92b9d13e90c544bbcf` (treea41d246d), on one H200 `GPU-da0d9c21-eb80-f5c6-c12c-bfc5bcb9f207`. This dependency ablation does not establish an independent-main Tiny gain.

Checkpoint `inclusionAI/Ming-omni-tts-16.8B-A3B@2efcd28d04f83b1bd471af639b4210c9ecf2cd33`; provided `examples/configs/ming_omni_tts.yaml`, max-running8 / graph buckets1,2,4,8 / output budget256. Request seeds are omitted because the native API rejects them; startup RNG and engine seed42/43 are verified from actual CPU/CUDA seeds at capture. Concurrent requests are not individually deterministic. ASR and fixed Dense CAM++ score every output. Full-response AudioVAE remains compact eager; AR and acoustic-tail graph serving replays are verified in every arm, with AudioVAE serving replays additionally required in every streaming arm.

| Language | c | Stream | WER% control → PR | SIM control → PR | Edits control/PR at42;43 | Failed/attempted |
|---|---:|:---:|---:|---:|---|---:|
| EN | 1 | false | 0.7082 → 0.7082 | 0.810337 → 0.810337 | 3/3; 2/2 | 0/128 |
| EN | 1 | true | 0.7082 → 0.7082 | 0.810349 → 0.810349 | 3/3; 2/2 | 0/128 |
| EN | 8 | false | 0.5666 → 0.7082 | 0.811814 → 0.808386 | 2/2; 2/3 | 0/128 |
| EN | 8 | true | 0.5666 → 0.8499 | 0.811583 → 0.807644 | 2/4; 2/2 | 0/128 |
| ZH | 1 | false | 0.7745 → 0.7745 | 0.858970 → 0.858970 | 5/5; 4/4 | 0/128 |
| ZH | 1 | true | 0.7745 → 0.8606 | 0.859051 → 0.859051 | 5/5; 4/5 | 0/128 |
| ZH | 8 | false | 0.7745 → 0.5164 | 0.857665 → 0.858625 | 4/3; 5/3 | 0/128 |
| ZH | 8 | true | 1.8072 → 0.5164 | 0.847748 → 0.858058 | 2/3; 19/3 | 0/128 |

All 256 c1 paired WAV comparisons are hash-identical. The ZH streaming seed 43 WER difference is one ASR edit on identical WAV `10002698-00000106` (发展生/发展商), demonstrating scoring variability without an audio change. Means are arithmetic means of the two seed corpus scores. Native concurrency8 scheduling can assign global FlowLoss noise differently despite the same startup seed. Differences remain visible; no non-inferiority threshold or deterministic per-request equivalence is asserted. One ZH c8 streaming control output (seed 43,10002539-00000054) transcribed as 嗯 and has 16 edits versus 0 in the candidate; its paired recordings are retained. Zero failed requests means transport/model completion, not zero word errors or uniformly good quality. [All per-seed results and paired transcript differences](omni-analysis.json); [selected paired recordings](audio-examples.md) ([hash index](omni-audio-index.json)).

Every arm captured 4 AR + 4 acoustic-tail + 1 streaming AudioVAE graphs (the VAE graph is prepared at startup in both modes). Non-streaming requests do not replay the streaming VAE graph. Cost values below are observed subset-run ranges, not independent Tiny costs or a speedup claim.
- omni-control: startup 112.12–122.11s; peak device 106.526–106.708GiB; 9 captures/arm, graph-count increment0.
- omni-candidate: startup 112.09–118.14s; peak device 106.524–106.708GiB; 9 captures/arm, graph-count increment0.

Two operator-input preflight failures (unsupported request seed, then generic 2048 budget exceeding the provided 256 cap) occurred during warmup before formal requests and were retained separately. Production request guards and regression assertions were kept.

#3217 remains Draft: dependency landing and the independent full Tiny matrix/quality/cost qualification are still pending. This complete shared-model subset fills only the specific cross-model review request.

The shared-model assignment was released after verified off-node results/audio backup and process/cache cleanup; see [release receipt](omni-resource-release.json). The separate #3136 quality-repeat assignment is also released after its final verified backup and cleanup; see [quality release receipt](quality-resource-release.json). All 330 affected original/fresh transcript IDs have recordings retained off-node; the public report selects 14 representative Ming3 WAVs.

## Remaining gates

#3136 quality assessment and reviewer approval; #3217 prerequisite landing, independent Tiny c1/c16/c32/c64 × both modes × EN/ZH × two-seed ABBA performance/quality/cost qualification, then approval. #3217 remains Draft. After accepted series merges, the final merged-main versus frozen pre-series main validation remains required. Resources are active only for the current tests and are backed up off-node every300 seconds; release is recorded after each assignment's consumers finish.

## Prior complete records

- [Original92-arm non-streaming matrix and ablations](../ming3-nonstream-current-main/report.md).
- [c1/c32 first-packet and underrun evidence](../ming3-streaming-review/report.md).
- [Earlier current-main CUDA/HTTP integration](../ming3-current-main-integration/report.md).
- [CPU fallback regression and source records](../ming3-cpu-vocoder-fallback/report.md).
- [Tiny streaming functional records](../ming3-tiny-stream-integration/report.md).
- [Research provenance and original evidence index](https://gist.github.com/Zhuofeng-Li/ca0ebf3fc628f1921895867071befb34).
