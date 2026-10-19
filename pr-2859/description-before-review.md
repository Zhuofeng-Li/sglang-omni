## Motivation

MOSS-TTS Delay spends host time scheduling channel embeddings, sampling and codec decode between GPU steps. Against current main `85d4219916c5457995fc7ac3b53b7e5b5ab75ea0`, the remaining changes improve **non-streaming throughput by 39.9%** and **streaming throughput by 30.0%** on one H100 80GB at concurrency 16.

The updated port fixes the current runtime-context TP query and reserves graph-capture headroom by reducing the default AR stage fraction from 0.72 to 0.60. The uncorrected merged candidate exhausted memory during prefill capture and then failed requests on the removed TP helper; both failures were retained. Both measured variants use the same 0.60 budget. Startup increases by about 37 seconds and sampled peak VRAM by about 3.7 GiB. Non-streaming SIM decreases slightly; all repeat results are retained below.

## OpenRSI-Index / RSI-Harness provenance


Developed and evaluated by an autonomous research agent using [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness), from [OpenRSI proposal #154](https://github.com/OpenRSI-Foundation/OpenRSI-Index/discussions/154). This ports Claude Code run [eaefbfb7928074d3, accepted submission agent-6](https://openrsi-handoff-nsl.rsi-anything.workers.dev/tasks/sglang-omni-moss-v1.5-runtime-d154/runs/eaefbfb7928074d3).

Original research source: `1523543056bf334bc2f4d69db23aad0a002cedf2`; port base: `fef24ecf5e5ac84c22e7ab3b3b6e5d4861386317`. Reconstruction recovered 13 changed source files and matched the evaluator's complete source inventory SHA-256: `f02a5b5c27e0d11f5736378f8f55e321a07671c10fa8d836781f125248bbb8a4`. The [benchmark report](https://github.com/Zhuofeng-Li/sglang-omni/blob/767c1611d49e478d85f6c5b662423984323d732f/docs/benchmarks/moss_tts_delay_runtime.md) records the protocol, per-seed results and adaptation limits.

The new matched evaluation is direct PR qualification, not another RSI-Harness research run or a new formal Judge acceptance.

## Modifications


- Fuse compatible TP1 fp16/bf16 channel embeddings with ordered dtype rounding and an eager fallback.
- Capture default-profile full-vocabulary mixed sampling, and enable the existing one-step decode lookahead for compatible batches of at least two requests.
- Batch output-row copies to CPU; fence pinned upload reuse and retain graph inputs/feedback storage through resolution. Skip completed requests and roll back retracted launches.
- Capture exact prefill lengths 1–512 and single-segment non-streaming vocoder lengths 1–128 in the default colocated layout. Keep multi-segment eager batching, capture-failure fallbacks, platform graph opt-outs, and the bounded single-process configurations.
- Add regression tests, documented opt-outs, and a [provenance/benchmark report](https://github.com/Zhuofeng-Li/sglang-omni/blob/767c1611d49e478d85f6c5b662423984323d732f/docs/benchmarks/moss_tts_delay_runtime.md).

- Adapt the TP1 embedding guard to `get_parallel().tp_size` and test the CUDA model request path and eager fallback.
- Leave 12% of card memory outside the default stage budgets for dense graph capture; retain existing single-process policies.

## Benchmark & Profiling

Fresh paired qualification: latest main `85d4219916c5457995fc7ac3b53b7e5b5ab75ea0` versus the original PR merged onto it, with the TP query repaired and AR stage fraction 0.60 in both variants. This PR now encodes that tested candidate configuration as its default. See the [full report](https://github.com/Zhuofeng-Li/sglang-omni/blob/767c1611d49e478d85f6c5b662423984323d732f/docs/benchmarks/moss_tts_delay_runtime.md) and [all repeat summaries/protocol](https://github.com/Zhuofeng-Li/sglang-omni/blob/9b45def1072934334648f33395184c95270adee6/docs/benchmarks/moss_tts_main_incremental_20261016.json).

One H100 80GB HBM3 on Radix; PyTorch 2.13.0+cu130, SGLang 0.5.21, Transformers 5.12.1. Full SeedTTS English split, 1,088 requests × seeds 42/43/44 × both modes × both variants: **13,056 requests and quality-scored clips**, zero failed/skipped. Client concurrency 16, running/decode-graph caps 64, 16 excluded warm-ups, 2,048-token cap, references-format cloning and automatic token count. Every pass starts a fresh service with empty compile/JIT caches; same card and OMP/MKL threads 8 under shared CPU scheduling. Main runs first for seeds 42/44 and candidate first for seed 43. Model/data/scorer revisions are recorded in the JSON.

Arithmetic means of repeat-level metrics, including corpus WER and percentiles:

| Metric | Main non-streaming | Candidate non-streaming | Main streaming | Candidate streaming |
|---|---:|---:|---:|---:|
| Requests/s | 11.736 | 16.415 | 9.376 | 12.190 |
| Mean latency (s) | 1.356 | 0.969 | 1.698 | 1.304 |
| p95 latency (s) | 1.713 | 1.212 | 2.134 | 1.632 |
| Mean first audio (s) | — | — | 0.7259 | 0.6073 |
| p95 first audio (s) | — | — | 0.8412 | 0.6976 |
| Corpus WER (%) | 1.7611 | 1.7332 | 1.8142 | 1.7249 |
| WavLM SIM (cosine ×100) | 69.0594 | 68.9953 | 68.9874 | 69.0849 |
| Startup (s) | 92.06 | 129.08 | 92.06 | 129.42 |
| Sampled peak VRAM (GiB) | 67.12 | 70.86 | 66.94 | 70.63 |

All four mode/variant seed-42 quality runs exceed 2% WER individually; all four mode/variant three-repeat means are below 2%. No outlier filtering. The benchmark reports zero token-cap hits but does not observe finish reasons, so it does not independently prove zero truncation. Peak VRAM uses 10-second sampling. WER and SIM do not establish listening equivalence. Other hardware and concurrency levels remain unmeasured.

The historical **1.8628×** result belongs to the original experiment against `1523543056bf334bc2f4d69db23aad0a002cedf2`; it is not the incremental gain on current main. Its complete performance/quality/provenance tables remain in the report.

## Related Issues

#2780 remains an open alternative prefill/async-decode implementation from a different run. This update continues #2859 and preserves its own provenance; it does not open a duplicate PR or attribute independent gains to individual components without ablations. Proposed landing order: #2859 first, then reconcile #2780 to one prefill/async-decode implementation and qualify only its remaining increment against the landed baseline. Agreement is pending in [the review follow-up](https://github.com/sgl-project/sglang-omni/pull/2859#issuecomment-6235412575); #2780 is held from merge until reconciliation and paired Delay evaluation.

## Accuracy Test

- Full paired generation, Qwen3-ASR-1.7B WER and WavLM SIM: **13,056/13,056** clips, no failures/skips. Quality scoring runs after TTS serving stops.
- MOSS-TTS CPU suite plus shared async-decode/model-runner hooks: **393 passed, 4 skipped, 96 deselected**.
- Embedding, sampling-graph and vocoder files on the H100: **95 passed**, including the new CUDA runtime-context/eager-fallback regression.
- Updated PR defaults without comparison YAML: **4/4** end-to-end smoke requests succeeded.
- `pre-commit run --all-files` and `git diff --check`: passed.

## Checklist

- [x] Format your code according with pre-commit.
- [x] Add unit tests.
- [ ] Update documentation / docstrings / example tutorials as needed. No `docs/` changes are included.
- [x] Provide throughput / latency benchmark results and accuracy evaluation results as needed.
- [ ] For reviewers: If you haven't made any contributions to this PR and are only assisting with merging the main branch, please remove yourself as a co-author when merging the PR.

## CI

Current head: `767c1611d49e478d85f6c5b662423984323d732f`. This documentation-only follow-up renames the Delay report and documents restoring the 0.72 AR stage budget with capture disabled. Runtime and published benchmark artifacts are unchanged. The integrated main revision remains `49dc4ba9628b8a8827be060b4175afdea925c7c9`; the actual upstream main tip observed during this follow-up is `6bdd47967caa55c38430d18175b750008aecab61`, which is not represented as a newly validated integration revision.

Local validation: all applicable full-repository pre-commit hooks passed (the private-key hook was rechecked across all files after the index changed during the initial run), changed-document hooks passed, and `git diff --check` passed. The cookbook YAML was loaded through `ConfigManager.from_file`: stage budgets resolve to 0.10 / 0.72 / 0.18, with prefill capture disabled, async decode false and segment capture 0. Relative report links were checked. No new GPU benchmark was run for this documentation change.

New-head [Omni CI run](https://github.com/sgl-project/sglang-omni/actions/runs/39043301135), lint and documentation checks have been triggered and are pending. Current model-CI labels remain `run-tts-moss-tts-local-transformer-v1.5`, `run-tts-ci`. The required independent reviewer approval and landing-order agreement are pending.

Historical integration evidence for parent `988e9f0f538b5a5e5e097790bb5583b240799312`: [Omni CI run](https://github.com/sgl-project/sglang-omni/actions/runs/38956555111) passed CPU and accelerator unit tests, non-streaming TTS, streaming TTS, consistency and serving stress. Scoped CPU MOSS tests had 131 passed and 13 accelerator tests deselected. Those results are parent-revision evidence, not a completed new-head check.

The supported MOSS model-CI preset tests LocalTransformer, while this PR targets Delay. Those model-CI results do not replace the recorded paired Delay measurements above. The dedicated first-audio latency stage is Qwen-only. Published performance measurements retain their recorded benchmark revisions.

Co-authored-by: Kangda Wei <59715925+WeiKangda@users.noreply.github.com>


### Documentation removal

Current head: `1894fa88fa8b09392b0aa0625eec34aae3e95edd`. All `docs/` changes have been removed from this PR. Runtime, configuration and test files are unchanged by this revision. Performance results above retain their recorded source revisions and measurement scope; benchmark-report links pinned to earlier commits refer to historical evidence. CI for this new head is being rechecked.
