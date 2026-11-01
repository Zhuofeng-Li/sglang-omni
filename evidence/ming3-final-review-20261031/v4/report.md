# Ming3 resolved-default review verification

Measured 2026-11-01 UTC on one dedicated Radix H200. #3189 source `e00107f8d5abf7cec043b1cb9607d939af79aefc`; final #3190 source `6b6cee66f0a79b86b5dea236fcce40b3283506d5`; actual upstream main `e354ea41fd1d49f400f453298a352e56ec35c1e9`. Each worktree's1716 tracked runtime/test/configuration files were hash-matched against its uploaded test source. #3189's full main-relative diff has14 files; #3190's diff against the updated dependency has3. Neither contains doc/docs changes.

## Review fixes

#3189 makes all shared scheduler errors refer to AudioVAE and removes the unused20-line `ming_tts.audio_upsample` reexport. Runtime/tests use the shared module; the other legacy adapters and factory paths remain covered. The preexisting cookbook patch was preserved outside the upstream PR and withdrawn under the contributor's no-doc/docs policy. Startup guidance: one GPU for both checkpoints/backbone and AudioVAE; Tiny CPU preprocessing with one worker; Dense GPU preprocessing with four workers. This guidance is recorded in the original PR description.

#3190 sets `enable_dense_streaming=dense` in the actual pipeline default stage factory. The low-level factory stays conservatively False; explicit overrides and CPU vocoder fallback remain available. The consumer regression creates a local checkpoint config, resolves a real default pipeline, invokes the engine factory and checks actual result/stream routing and CPU full-latent decode. It does not call only the output builder.

## Results

- #3189 focused AudioVAE/Tiny/Dense suites:101 passed; no skips.
- #3190 before-fix control (only remove the default enablement line):5 expected default Dense route assertion failures,34 passed,15 deselected. Includes CUDA/legacy/custom and simulated XPU placement cases; simulated placement is not real XPU validation.
- #3190 final integrated focused suites:99 passed; no skips.
- Both final integrated sources pass full all-files pre-commit. The first #3189 formatter run changed the shared file; the final clean pass is archived.
- Default-pipeline real Dense0.5B HTTP smoke:14 PCM requests succeeded, plus SSE and disconnect exercise; EN/ZH, with/without reference, streaming/nonstreaming, concurrency4, cancellation and next-request recovery, and a1-latent length-stop flush. No YAML or override enables Dense streaming in this launch. The launch only sets host/port, memory fraction0.6 and capacities32. Inherited MPS is off.
- SSE emits3 nonempty audio events at128.139/177.302/213.706ms, before the terminal event at213.801ms (`stop`,31 generated tokens). This single functional sample is not a latency benchmark.
- The1-latent length stop emits3528 samples and reports `length`. All four EN/ZH reference/nonreference offline-versus-stream pairs have equal sample lengths; PCM is not bit identical (correlations0.99075–0.99967). The regression separately checks reference-conditioning latents are excluded from emitted generated data; no full-corpus quality equivalence is claimed.
- Cold startup139.462s is a single functional launch, not an ABBA cost comparison. Server exits0; visible GPU memory returns0MiB. Python warns about one semaphore at process shutdown; retain this warning rather than calling all IPC cleanup perfect.

## Runtime and evidence

Official current CI image `hongccc/sglang-omni@sha256:06ed306707bcf3d9e9beb5ba7ce66f09a666cac11c23455ece50c34199c0e985`: Torch2.14.1+cu130, SGLang0.5.22, Transformers5.19.0, FlashInfer0.7.1. Frozen Dense checkpoint `inclusionAI/Ming-3.0-tts-0.5B@8d66b70a00f05ad183fa8a863b4ce609fc83cbc0`; SeedTTS Arrow `27f4c1adee83b5b29b7c4b375f6b976324bda308` (first two rows per language for functional smoke). Model and data are downloaded once with HF CLI and reused.

[Raw result archive](latest-results.tar.gz) SHA256 `613a6f82eab68f67f9f867c6724c661f67626c35afb3e8fbbce60c4f9ce9645a`. Logs include the expected pre-fix failures and initial setup failures: the first allocator test could not import an omitted sparse-checkout package, and the first HTTP attempt had a host-absolute asset symlink unavailable inside its container. Both occurred before their corresponding checks; neither is counted as passed. Corrected full Python source and relative asset mount were used for successful verification. The archive also contains separate SGLang allocator checks; these are not Ming performance results.

The [prior full qualification](../v3/report.md) remains attributed to its original frozen main/candidate commits and date. Current source includes subsequent shared-main changes; old corpus metrics are not relabeled as measurements of these review heads. Required new-head CI/review and final actually-merged-main overall paired validation remain outstanding. Meta Omni is excluded by user instruction.


## Later base observation

Upstream main advanced to `e5b87a8fe91f25fa62c229809484b48d8c748c18` during publication. Its107-file diff from the tested base touches other model families, MLX, docs/workflows and CPU Whisper backend validation. The CPU platform change adds a Whisper-only guard after the same inherited backend policy; it does not alter the Ming CUDA/CPU-vocoder paths. Ming3-TTS and the shared AudioVAE source files are unchanged. New CI synthetic integration remains independently tracked; these tests retain the actual `e354ea41` integrated base.
