# Ming CPU vocoder fallback repair

Reviewer thread: https://github.com/sgl-project/sglang-omni/pull/3189#discussion_r4396752939

The streaming AR adapter dropped full latents whenever the HTTP request had stream=true, including configurations using a CPU vocoder. The CPU vocoder uses SimpleScheduler and needs the complete latent tensor, so it failed at the final decode. The repair derives use_streaming_vocoder from the resolved downstream vocoder configuration, including the legacy factory alias. CPU and custom full-decode vocoders receive the complete final latent tensor and no unused incremental chunks. Default CUDA vocoders keep the existing stream builder and omit the full final tensor as before.

## Validation

- The added regression fails on pre-fix source 827f2084, and all 10 parameterized cases pass after the repair. The cases cover Tiny/dense checkpoints, old/new vocoder factory aliases, stream=true CPU fallback, CPU non-streaming and unchanged default CUDA streaming dispatch.
- Related suites on the Tiny feature branch: **94 passed, 11 accelerator cases deselected**.
- Conflict-free cumulative integration of repaired top 292d54e0bf0da2bf238030a652c414eb83fcfb74 with main 57f12ffe2ee9a6d229a88047875127c9660e49ce (tree da3247d0e8e8712b6a318f825a5e904b31770e1b): **575 passed, 49 accelerator cases deselected**. This covers all Ming-family CPU tests, stage routing, model capability/checkpoint contracts, moved speculative modules and shared device graph host tests. No assertions were relaxed.
- Full pre-commit run --all-files passed on both the Tiny repair and the rebased top.
- The new regression stubs the external GPU engine infrastructure and runs the actual result adapter plus a real small CPU AudioVAE, comparing complete audio samples and terminal metadata. It is not a real-checkpoint GPU-to-CPU deployment benchmark. Current-head accelerator CI remains a separate required gate.

## Source and evidence reuse

Published heads are recorded in cpu-vocoder-code-published.json. #3136 remains d1be1e0c; #3189 becomes 6272ee4c; #3190 becomes eebeb3b7; #3217 becomes 292d54e0. All original PRs and dependency order are preserved. Full per-PR file lists were checked; only the previously requested Ming cookbook is under doc/docs, and this fix adds no documentation changes.

No new performance measurements are claimed. Existing c1/c32 CUDA first-audio/underrun and #3136 paired measurements retain their actual measured source IDs. The default CUDA routing is unchanged; the CPU configuration now uses complete-response fallback. Main changes after ed09865a include speculative adapter moves, new model registry imports, other-model optimizations and ASR/session updates. The targeted host suites pass on actual main 57f12ffe, but additional eager model imports can affect startup cost: old cost figures are not relabeled as fresh measurements on this main.

#3217 remains draft: independent c1/c16/c32/c64 × EN/ZH × both modes, two-seed ABBA performance/quality/cost qualification is still pending after prerequisites land. Final merged-series comparison is also pending. All earlier task GPU assignments were released; this CPU repair did not allocate another GPU.
