## Motivation

Add incremental audio output to `inclusionAI/Ming-3.0-tts-0.5B`; current main waits for complete latent generation before returning audio.

Depends on #3189 (Tiny streaming). This PR targets its branch for an isolated 0.5B review diff and will retarget main after it merges.

## Modifications

- Enable the dense checkpoint's single-latent generation path with the shared incremental AudioVAE decoder.
- Reuse existing reference-audio/text conditioning and emit generated latents only.
- Add regression coverage for excluding reference prompt latents and for flushing the checkpoint's five-step minimum normal utterance.

Streaming stays opt-in per request. Both checkpoints generate one latent per autoregressive step; VAE interpolation is a separate operation. Sampling, weights and non-streaming full-sequence decoding are unchanged.

## Validation

Tested October 25, 2026 on one NVIDIA H100 80GB HBM3 at `23a5e2930d1ea074fc027a005a605a8deefc72d1`. PyTorch 2.14.1, SGLang 0.5.22, Transformers 5.19.0 and Diffusers 0.37.0. Model revision `8d66b70a00f05ad183fa8a863b4ce609fc83cbc0`; SeedTTS Arrow revision `27f4c1adee83b5b29b7c4b375f6b976324bda308`; seed 42. Automatic pipeline config, max running requests / graph batch size 8 and memory fraction 0.6.

- **28 tests passed** in `tests/unit_test/ming3_tts` in the pinned H100 environment. Full `pre-commit run --all-files` passed.
- Four EN/ZH × no-reference/reference cases at concurrency 1: final non-streaming PCM is byte-identical to clean main `b95690320de7187795e009cf8b3f25891a883274` for all four. Observed main `ff37c52` adds default-disabled multimodal speculative hooks; those paths were audited and do not change this non-speculative Ming pipeline.
- All four streaming/full decode pairs retain identical sample counts. BF16 cached decoding is not bit-identical to full decoding: waveform correlations range 0.999535–0.999848.
- **14 completed raw-PCM requests**, one successful SSE request and one intentional disconnect per model: four paired cases, four concurrent reference-conditioned streams, disconnect recovery and a one-latent length-capped stream. SSE usage and actual stop/length reasons passed. Configured length-cap outcomes are retained.
- Qwen3-ASR-1.7B revision `7278e1e70fe206f11671096ffdd38061171dd6e5` produced identical normalized transcripts for all four streamed/full pairs. This is a small functional check (one SeedTTS target per language, with and without reference), not full-corpus quality qualification. Repository normalization is word based for EN and character based for ZH:

| Case | Full → streaming WER / CER |
| --- | --- |
| EN without reference | 0.00% → 0.00% |
| EN + reference | 0.00% → 0.00% |
| ZH without reference | 4.55% → 4.55% |
| ZH + reference | 4.55% → 4.55% |

No throughput or model-quality improvement is claimed. Other accelerators were not validated. Validation results and recovery artifacts are preserved outside the upstream patch; the Radix assignment was released after checking zero GPU memory and no remaining containers.

## CI

Select `run-unit-test-ci-only`: H100 CPU partitions and accelerator unit tests, plus automatic PR checks. The latest CI guide/resolver/workflows and live labels were checked; there is no Ming3 TTS end-to-end preset. Dedicated Radix tests above cover the target model. Current CI (head `23a5e293`): [Omni CI run 40237981227](https://github.com/sgl-project/sglang-omni/actions/runs/40237981227) has passed preflight and environment setup; H100 unit jobs are queued/running. Preflight checked out this exact head and resolved `run_unit_test=true`, `run_tts=false`, with no model preset. Initial unlabeled gate runs were superseded by these explicitly selected runs. Automatic lint, test layout, docs build and Rust checks have passed; NPU builds remain in progress. No `doc/` or `docs/` paths are changed.

