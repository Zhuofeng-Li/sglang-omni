# Ming3 final integration review — 2026-10-31

> Historical qualification notice: Historical source before main #3355; superseded by the main740 qualification and default-MPS-off review. See [active default-off qualification](v3/report.md).
Status: qualification is running. This record is staged locally and is not a final pass report.

## Scope and source identities

The requested compact cells are full SeedTTS EN at concurrency 16 and ZH at concurrency 1. Each comparison uses seeds 42 and 43 in A42, B42, B43, A43 order. The 16-arm plan separates actual-main → #3136 performance from non-streaming → streaming quality on the same final #3190 tree; the latter is not an independent performance comparison with main. Different language/concurrency cells must not be combined into a geometric throughput result.

- Frozen actual main: `7537f89baca54d19de2b7afe5465bb614c10b625`.
- #3136: `94092b37409c85b96deb1ec23f94eda957417220`.
- #3189: `c2ea3f8a6bbfff80d05e2a23b2c86e425f5ab2df`.
- Final #3190: `08f6a11201074948de8320ec14ead37cb9dd2053`.

The node source files and symlinks were checked against all archived regular files; archive SHA256s match the controller source manifest. Source trees are mounted read-only. Runtime is the exact shared `ming-final-review:20261031-v2` image, ID `ac156988391231d261f4ad0d0f078c59181a7a29058021e0ad1c1812e3d667ca`; see the runtime freeze for dependencies. The newer observed main `d53e10b8` changes only Qwen3-TTS reference encoding and its tests. These remain measurements of the explicitly frozen main, not relabeled newer-tip measurements.

## Fixes

The #3136 conflict retains both the PCI locality constant and main's video decode thread limit. The intermediate #3189 no longer rejects dense stream=true: dense incremental decoding defaults off there and the complete-response fallback retains full terminal latents. #3190 enables incremental dense decoding by default. CPU-vocoder full decode fallback remains available. Both feature PRs retain coordinated landing order.

## Reproducible protocol

One dedicated Radix H200, GPU UUID `GPU-99e2ecd1-862a-4af1-222d-841708198f30`; one serial service at a time. The separate B200 research task is untouched. No CPU quota or affinity overrides. Each arm has fresh compilation and reference caches; model/dataset assets are reused. Native warmup equals concurrency. Automatic model-specific pipeline settings and the explicit overrides in the recorded YAML/command are retained; defaults differ between actual main and the candidate as disclosed by their resolved pipeline records. Native max-running and graph batch limit are both 64; max output tokens are 2048. Startup includes the common capture-event instrumentation. Capture counts mean successful capture_end events, not necessarily unique retained graphs. Device memory is the maximum observed under nominal one-second polling; actual polling gaps and raw samples are retained.

- Ming 0.5B revision: `8d66b70a00f05ad183fa8a863b4ce609fc83cbc0`.
- Qwen3-ASR-1.7B revision: `7278e1e70fe206f11671096ffdd38061171dd6e5`.
- SeedTTS Arrow revision: `27f4c1adee83b5b29b7c4b375f6b976324bda308`; full EN 1088 and ZH 2020 rows, with reference conditioning.
- WER is corpus edits/reference units, computed by the native ASR evaluator; SIM is cosine similarity from the pinned CAM++ model, 16 kHz native filterbanks, CPU ONNX inference with two intra-op threads.
- Report arithmetic seed means for req/s, latency mean, corpus WER and SIM. Keep seed p95s as ranges, never average percentiles. Retain output token totals, audio lengths, failures and costs. No quality acceptance margin is assumed.
- Throughput is the native reported summary; raw records lack absolute per-request start/end timestamps, so it cannot independently be recomputed. Request/quality/SIM/audio-hash IDs, completion, errors and score arithmetic are independently checked in the artifact verifier. This is an artifact audit, not a rerun.
- Audio hashes record generated WAV identity; WAV files themselves remain on the assigned node and are excluded from the minimal off-node archive. Model weights and runtime caches are also excluded.

The original first-arm setup attempt failed before any requests because offline model metadata was incomplete. It is retained separately; full snapshots were then completed and reused. No measured request failed in that setup attempt and it is not counted as a completed arm.

## Results

EN c16 actual-main/#3136 ABBA is complete: req/s 8.9425 → 42.2735 (+372.73%); WER 1.034079% → 0.988026%; SIM 0.779218 → 0.777064; failures 0/2176 → 0/2176. Startup mean 93.62 → 140.16 s; peak GiB by seed 107.4717/107.4736 → 108.8896/108.8213; graph capture events 19 → 430. Audio duration mean 3.94165 → 3.90107 s (-1.03%). Other blocks remain pending. See `paired-block-summary.json` and the raw result archive when published. Partial arms do not establish a paired conclusion. Actual main contains the previously identified sampling-scale lifetime bug; native-main differences do not isolate that correctness fix from the other optimizations. Prior corrected-control experiments remain historical evidence, not replacements for this actual-main pair.

## Validation and CI

Final integrated relevant GPU/host regression suite: 310 passed, zero skipped. Intermediate fallback host suite: 54 passed, one accelerator case skipped. Full pre-commit passed. The broader controller CPU environment lacked a new Torch stream-priority API; those cases pass in the pinned GPU runtime. All three current-head Omni CI runs passed: #3136 run 41222530747, #3189 run 41222531893, #3190 run 41222533557. Unit checkout revisions and counts are recorded separately. #3136 also passed the Higgs non-streaming MPS stage on exact head 94092b37: 1088 canonical requests, zero failures, overlap and configured gates passed; all MPS GPU/process/port/state cleanup checks passed. This is shared-path coverage. The separate ephemeral-home cleanup job is workflow_dispatch-only and therefore skipped for these pull_request events, independently of selected model stages; it is not counted as passed. The #3190 accelerator job checked synthetic merge `0683fc1b718a8c312a1ee12c457d2379ab0231c2`, whose tree exactly matches the final measured head. The #3189 completed jobs checked `e0415b51bceeb1b0ab288eca658e6ad5ef525560`, whose tree matches the intermediate head. Model end-to-end corpus checks are the dedicated Radix runs, not other-model CI presets. Actual current-base/cumulative source comparisons contain no doc/docs modifications. GitHub #3189 still reports the old base snapshot 02103f98 and a 186-file list containing upstream documentation, while the actual target branch 94092b37 comparison contains 15 code/test files and no docs. A same-base refresh is rejected because this is a native stack. Metadata and complete file lists must be rechecked before landing; do not remove upstream documentation to compensate. Only the validated prefix #3136 → #3189 → #3190 is in scope; draft #3217 remains excluded. Human review remains pending; no readiness claim is made.

## Earlier evidence

Earlier results and source identities are retained in the [non-streaming archive](../ming3-nonstream-current-main/report.md) and [streaming archive](../ming3-streaming-review/report.md), including corrected-control and optimization ablations. They are not new-head measurements.
