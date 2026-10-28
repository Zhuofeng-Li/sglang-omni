# Ming CPU vocoder fallback repair

Reviewer thread: https://github.com/sgl-project/sglang-omni/pull/3189#discussion_r4396752939

The AR adapter dropped complete latents whenever stream=true, including configurations using the standard CPU vocoder. The CPU vocoder uses SimpleScheduler and requires the complete tensor, so final decoding failed. The pipeline now derives use_streaming_vocoder from the downstream standard vocoder configuration, including the legacy factory alias. Standard CPU vocoders receive complete terminal latents without unused incremental chunks. Standard non-CPU and custom vocoder factory routing retain their existing behavior.

## Current validation

- **13 parameterized regression cases pass**: Tiny/dense, old/new factory aliases, CPU streaming/full-response fallback, CUDA dispatch, a mocked XPU routing case, and custom GPU factory routing. Negative checks reproduce the original CPU bug and verify that custom factory dispatch is preserved. The original CPU reproduction fails on 827f2084.
- Related feature suite: **97 passed, 11 accelerator cases deselected**.
- Final top eadc7611f6d3647db889000ca86c0c94a7ff518a integrated conflict-free with main 57f12ffe2ee9a6d229a88047875127c9660e49ce, tree 5f9d74c484a637ab732ffe7e2a4ab82ca6d018f5: **578 passed, 49 accelerator cases deselected**. Coverage includes all Ming-family host tests, stage routing, model capabilities/checkpoints, moved speculative modules and shared device-graph host tests.
- Subsequent main **3bbae06faa28acedd56d2d942a962d7bcff5bc49** adds Qwen speaker embeddings through shared speech validation. The cumulative final top merged conflict-free into local tree **ce49420fe7ccdbc7706a3be978430eacc8d4e6de** and passed **360 tests, 2 skipped, 34 accelerator cases deselected** across the speech protocol/API, Ming3 and model capabilities. The initial M4A failure came from missing TorchCodec and FFmpeg shared libraries in the isolated host environment; adding repository-pinned torchcodec0.17.0+cpu with av19.0.2 bundled libraries restored the test without source or test changes. Command/environment/result and test output are archived beside this report. All four original PR bodies include this scoped host result. It is not a fresh CUDA or performance measurement.
- Full pre-commit run --all-files passed on the final cumulative branch; modified-file checks passed on the feature repair. No tests or assertions were relaxed.
- The regression stubs external GPU engine infrastructure and executes the actual result adapter and a real small CPU AudioVAE, checking audio samples and finish reason/usage. The XPU case mocks platform selection: it is not XPU inference validation. This is not a real-checkpoint GPU-to-CPU deployment benchmark. Final CI results are reported per original head below; #3189 workflow completion remains pending.

## Published heads and CI

| PR | Current head | Current Omni CI |
| --- | --- | --- |
| #3136 | d1be1e0cbd4c939383fe75e3cc8799962996f240 | Previous successful run 40588559793; head unchanged |
| #3189 | a821f8945d6400506b5696460566de88df7e2621 | 40696735289; pending |
| #3190 | 432d34bafbf275a2a8b2850bed6bdb817ebe4ad1 | 40696735571; success |
| #3217 | eadc7611f6d3647db889000ca86c0c94a7ff518a | Manual 40696840691, unit-only; success |

Final #3190 CI passes on actual synthetic stack merge 0965c38cd02b4ba4c03029f7f2801c2fea1f5729 (tree9f3a832af6c503ab993151a91e09886945b77db2, includes main57f12ffe): CPU-A4730pass74skip, CPU-B5691pass49skip, accelerator1177pass28skip. All13 new fallback/routing cases executed and passed in CPU-B. Each unit job completed its own GPU cleanup and post-job steps; model stages and their ephemeral-home cleanup are N/A for this verified unit-only selection. Receipt with job IDs, checkout SHA and regression lines is archived alongside this report. #3217 manual unit-only workflow40696840691 also passed, with all partitions on exact current headeadc7611f6d3647db889000ca86c0c94a7ff518a, tree61fcc46aebaab28630788f7f14f202827275d453: CPU-A4718pass74skip, CPU-B5601pass49skip, accelerator1159pass34skip. All13 fallback/routing cases passed in CPU-A; final ephemeral-home cleanup job122864863661 and unit post-job/container steps succeeded. #3189 final workflow remains pending.

The original PRs and native stack3254 are preserved. Complete remote file lists are verified in cpu-fix-final-remote-files.json; counts remain 17/13/2/22 and the only doc/docs path is the explicitly requested Ming cookbook. This repair adds no documentation changes to the upstream PRs. Earlier local receipts and CI preflights in this directory preserve their actual superseded source IDs and are not passes on these final heads.

## Scope and remaining qualification

No new performance measurement is claimed. Existing c1/c32 CUDA first-audio/underrun and #3136 paired measurements retain their actual measured sources. Default CUDA routing keeps the same stream builder and omits the complete terminal tensor; only standard CPU vocoders regain complete-response fallback. Main changes after ed09865a include speculative module moves, other-model work and new model registry imports. Host tests pass on actual main57f12ffe and the targeted API/Ming audit on main3bbae06f; new eager imports can affect startup, so historical cost figures are not relabeled as fresh measurements on this main.

#3217 remains draft. Independent c1/c16/c32/c64 × EN/ZH × both modes, two-seed ABBA performance/quality/cost qualification is pending after prerequisites land. The final merged-series comparison and human approvals are pending. All prior task GPU assignments were released; this repair did not allocate another GPU.
