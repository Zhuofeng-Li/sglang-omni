# Ming review follow-up — 2026-10-28

Status: current-head code/CI checks complete; requested quality validation is running. This report does not qualify #3217 for release.

## Source and correctness

Original PR heads: #3136 `02103f988e5fc5d50e507318f66dbcdeb879931d`, #3189 `e2d7a33a63d8dba2d3410dea82677909e974b8c5`, #3190 `d57f2e970df64266b04e09bf716ba0ecc2342eca`, #3217 `96957d08e9dcd260005f5e92b9d13e90c544bbcf`. Integration base is main `61a23967f010de309e65e6f1b1c3819be4b51e86`. Later main `c7b09e42` changes documentation tooling and Qwen3-TTS only; frozen paired blocks are retained.

The shared decoder preserves main's Triton BTH upsample implementation at its common-module path, with compatibility exports at the old Ming-TTS import path. The new upsample test imports the defining shared decoder module; assertions are unchanged. Cumulative candidate tree `a41d246dc14e476e4aaff18088e99cba76910fd7` passed 276 Ming3/Ming-TTS tests, 6 skipped, on H200. Full pre-commit passed. The final attribution-only commit has identical Python ASTs to parent `a1c337c0` in all three affected files and names Zhuofeng Li in all five new notes.

## Current CI

The four linked records verify actual test checkout SHAs, parentage, pass/skip counts and unit post-job cleanup. Runs: #3136 [40749897047](https://github.com/sgl-project/sglang-omni/actions/runs/40749897047), #3189 [40749898756](https://github.com/sgl-project/sglang-omni/actions/runs/40749898756), #3190 [40749899471](https://github.com/sgl-project/sglang-omni/actions/runs/40749899471), #3217 [40750866735](https://github.com/sgl-project/sglang-omni/actions/runs/40750866735), all successful. #3217 is manual unit-only dispatch while Draft; its automatic Draft gate is expected and is not a passing check. No checks or protection were bypassed.

#3136 additionally passed the actual MPS/Higgs preset on exact head02103f98. Saved artifact12846337026 confirms1088 canonical requests,8 overlap-canary requests, quality guards and full process/port/MPS cleanup. This is cross-model lifecycle coverage, not Ming target-model validation. There is no Ming3/Ming-Omni-TTS preset; other model presets are not substitutes.

## #3136 requested quality follow-up

[Inspection](paired-error-inspection.json) of the existing paired ASR outputs confirms ENc16 +2/+6 net edits and ZHc1 +8/+12 (seeds42/43). Segmentation, number rendering and lexical changes are all present. Original WAVs were not retained after the old assignment was released; original hashes and transcriptions remain. No claim of listening to those original recordings is made.

Fresh full-split ABBA plus repeated same-seed corrected controls are running on one H200. Actual historical source identities are control `0d6a414e5e15c996900620d263143c89e0dd8acd`, candidate `3f8593f4cae19fe1c71e929a854bdc03b2c185e6`; model `inclusionAI/Ming-3.0-tts-0.5B@8d66b70a00f05ad183fa8a863b4ce609fc83cbc0`; data `zhaochenyang20/seed-tts-eval-arrow@27f4c1adee83b5b29b7c4b375f6b976324bda308`; scorer `Qwen/Qwen3-ASR-1.7B@7278e1e70fe206f11671096ffdd38061171dd6e5`. These are frozen-source reproductions, not new speedup measurements on today's main. The CSV's legacy `whisper_text` column contains Qwen ASR output.

ENc16 all six arms completed,1088 requests each with zero failures. Fresh A/B error counts are121/117 at42 and121/124 at43. Repeated A controls have121/122 errors. Some exactly identical WAV files received different ASR transcriptions; this documents evaluator variability without establishing non-inferiority. ZHc1 remains pending. Full conclusions await both cells.

## #3217 requested shared-model validation

32 arms are running on a separate H200: first32 EN/ZH SeedTTS samples, c1/c8, both modes, A42/B42/B43/A43. Control is actual #3190 `d57f2e97` (tree64a386f4); candidate is actual #3217 `96957d08` (treea41d246d). This is a dependency ablation for the shared conditioning change, not an isolated-main Tiny performance claim.

Checkpoint `inclusionAI/Ming-omni-tts-16.8B-A3B@2efcd28d04f83b1bd471af639b4210c9ecf2cd33`; provided `examples/configs/ming_omni_tts.yaml`, max-running8/graph buckets1,2,4,8 and output budget256, matching its serving cap. Request seeds are omitted because the native API rejects them. Process startup RNG and engine random seed are fixed to42/43; concurrent requests are not claimed to be individually deterministic. Real post-ready AR/acoustic-tail replays and, in streaming mode, AudioVAE graph replays are required before a result is accepted. Full-response AudioVAE uses the native compact eager path. ASR and CAM++ score every output; the pinned Dense CAM++ asset is shared across arms.

Two preflight operator-input failures were retained: unsupported request seed and generic output budget2048 exceeding the model's cap256. They occurred during warmup before formal requests; the production API guards and tests were retained. The corrected queue is running and preserves failures separately.

## Remaining gates

#3136 quality-repeat completion and reviewer approval; #3217 shared-model completion, prerequisite landing, independent Tiny c1/c16/c32/c64 × both modes × EN/ZH × two-seed ABBA performance/quality/cost qualification, then approval. #3217 remains Draft. After accepted series merges, the final merged-main versus frozen pre-series main validation remains required. Resources are active only for the current tests and are backed up off-node every300 seconds; release is recorded after each assignment's consumers finish.
