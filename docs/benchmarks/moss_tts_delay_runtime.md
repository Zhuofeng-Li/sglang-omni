# MOSS-TTS Delay runtime optimizations and qualification

This change ports runtime optimizations from an evaluated MOSS-TTS v1.5
experiment. Fresh qualification against current main is reported first; the
historical experiment and its provenance remain separate below.

## Current-main incremental qualification (2026-10-16 UTC)

On one H100 80GB HBM3, the remaining runtime changes improve non-streaming throughput by **39.9%** and streaming throughput by about **30%** against main at `85d4219916c5457995fc7ac3b53b7e5b5ab75ea0`. These are fresh matched measurements, separate from the historical experiment below.

The initial merged candidate could not serve this workload unchanged: its default 0.72 AR memory fraction exhausted memory during dense prefill graph capture, and the first requests at a reduced budget failed because the tensor-parallel query still used a removed function. Qualification uses `get_parallel().tp_size` and an AR stage fraction of **0.60 for both main and candidate**. The PR now makes that candidate budget the default; the single-process configurations retain their existing policy.

Protocol: full SeedTTS English split, 1,088 requests per pass; both modes; seeds 42/43/44; client concurrency 16; running-request and decode-graph caps 64; 2,048-token limit; references-format cloning and automatic token count; 16 excluded warm-ups. Each pass starts a new service with separate empty compiler/JIT caches. Non-streaming precedes streaming; main runs first for seeds 42/44 and candidate first for seed 43. The same card and OMP/MKL thread count 8 are used under shared CPU scheduling, without CPU pinning or quota.

Core software: Python 3.12.15, PyTorch 2.13.0+cu130, SGLang 0.5.21, Transformers 5.12.1, FlashInfer 0.6.18. The environment sets CUDA_HOME to the installed CUDA 13 toolkit, provides its lib64/libcudart linker paths, and disables unused DeepGEMM JIT in both variants. Model, codec, dataset and ASR revisions, all repeat summaries, and evaluated source identity are in the [machine-readable results](moss_tts_main_incremental_20261016.json).

All 13,056 generated clips received Qwen3-ASR-1.7B WER and WavLM speaker-similarity scoring after serving stopped. Quality scoring shares one ASR service across passes; WavLM scores are cosine similarity ×100. Means below are arithmetic means of repeat-level metrics, including corpus WER and percentiles; percentiles are not pooled.

| Metric | Main non-streaming | Candidate non-streaming | Main streaming | Candidate streaming |
|---|---:|---:|---:|---:|
| Requests/s | 11.736 | 16.415 | 9.376 | 12.190 |
| Audio seconds/s | 52.581 | 73.544 | 42.008 | 54.614 |
| Mean request latency (s) | 1.356 | 0.969 | 1.698 | 1.304 |
| p95 request latency (s) | 1.713 | 1.212 | 2.134 | 1.632 |
| Mean first audio (s) | — | — | 0.7259 | 0.6073 |
| p95 first audio (s) | — | — | 0.8412 | 0.6976 |
| p95 inter-chunk interval (s) | — | — | 0.2325 | 0.1465 |
| Corpus WER (%) | 1.7611 | 1.7332 | 1.8142 | 1.7249 |
| Speaker similarity (cosine ×100) | 69.0594 | 68.9953 | 68.9874 | 69.0849 |
| Service startup (s) | 92.06 | 129.08 | 92.06 | 129.42 |
| Sampled peak VRAM (GiB) | 67.12 | 70.86 | 66.94 | 70.63 |

| Mode | Seed | Main / candidate requests/s | Main / candidate WER (%) | Main / candidate SIM |
|---|---:|---:|---:|---:|
| nonstream | 42 | 11.742 / 16.404 | 2.1938 / 2.1519 | 69.3383 / 69.1936 |
| nonstream | 43 | 11.753 / 16.402 | 1.4904 / 1.3983 | 68.7877 / 68.7269 |
| nonstream | 44 | 11.714 / 16.440 | 1.5993 / 1.6495 | 69.0524 / 69.0654 |
| stream | 42 | 9.369 / 12.137 | 2.3194 / 2.1519 | 69.2032 / 69.2465 |
| stream | 43 | 9.350 / 12.216 | 1.4485 / 1.3564 | 68.7576 / 68.9411 |
| stream | 44 | 9.409 / 12.216 | 1.6746 / 1.6662 | 69.0015 / 69.0670 |

Coverage: 12/12 full passes, 13,056/13,056 successful requests, no generation failures, no reported token-cap hits, and no skipped WER or similarity scores. Both variants exceed 2% WER in seed 42 individually, although every mode-level three-repeat mean is below 2%. No outlier clips are excluded. Finish reasons are not observed by this protocol, so zero reported token-cap hits does not independently prove absence of truncation.

Tradeoffs: candidate startup takes about 37 seconds longer and sampled peak VRAM increases by about 3.7 GiB at the matched 0.60 budget. VRAM is sampled every 10 seconds, not an allocator-recorded instantaneous peak. These results cover concurrency 16 and one H100; they do not establish other load levels, hardware, listening quality or formal historical Judge eligibility. This is direct PR qualification, not a new RSI-Harness research run.

### Publication validation

The updated default configuration completed a fresh four-request end-to-end
smoke without the comparison YAML. Local checks on the same H100 and pinned
software completed with:

- MOSS-TTS CPU suite plus shared async-decode/model-runner hooks: **393 passed,
  4 skipped, 96 accelerator cases deselected**.
- Embedding, sampling-graph and vocoder test files on CUDA: **95 passed**,
  including the new model-level runtime-context/eager-fallback regression.
- `pre-commit run --all-files` and `git diff --check`: passed.

The non-streaming SIM mean decreases by 0.0641 points on its 0–100 scale;
streaming SIM increases by 0.0975 points. These objective metrics do not establish
perceptual equivalence, and no listening test is claimed.

## Provenance

- [Run eaefbfb7928074d3](https://openrsi-handoff-nsl.rsi-anything.workers.dev/tasks/sglang-omni-moss-v1.5-runtime-d154/runs/eaefbfb7928074d3):
  Claude Code, Claude Opus 5.5, accepted submission `agent-6`.
- Historical source baseline: `1523543056bf334bc2f4d69db23aad0a002cedf2`.
- Port base: `fef24ecf5e5ac84c22e7ab3b3b6e5d4861386317`.
- Reconstructing the trajectory's source edits recovered 13 changed files.
  The resulting complete source inventory matched the evaluator's SHA-256:
  `f02a5b5c27e0d11f5736378f8f55e321a07671c10fa8d836781f125248bbb8a4`.
  This identifies the evaluated source, not the subsequently adapted port.

## Changes retained in the port

- Fuse the 33-channel embedding gather/sum, preserving rounding after each
  channel addition. Use it only for compatible, unquantized TP1 fp16/bf16
  embedding tables; retain the eager path otherwise.
- Capture full-text-vocabulary sampling for default-profile mixed text/audio
  batches, retaining the eager mask, top-k/top-p, tie, and seeded-draw semantics.
- Use the existing scheduler's one-step decode lookahead at batch sizes of at
  least two when a compatible sampling graph is available. Retain launched
  state until resolution, restore retracted requests, and skip finished rows.
- Copy generated channel rows to CPU in one batch and fence pinned metadata
  buffer reuse. Keep feedback embeddings and output rows alive across launches.
- Capture exact prefill token counts 1 through 512 for the default colocated
  layout. Longer prefills use the existing eager fallback.
- Capture exact non-streaming vocoder lengths 1 through 128 for a single
  segment. Multiple segments retain current upstream's batched eager decode;
  uncaptured lengths and capture failures use eager decode. Graph inputs and
  position/RoPE caches remain alive for every replay.

Current upstream already uses persistent streaming codec sessions and a
dedicated reference-encoding stream. Those implementations are retained. The
experiment's older overlap-window streaming decoder and reference-stream edits
are therefore not restored. Single-process configurations, including the bounded
24 GB and 32 GB examples, do not enable the new dense prefill/segment ladders.

The older experiment reported about 50 seconds / 2.7 GB of additional prefill
capture cost and 15 seconds / 0.3 GB for segment capture. These are historical
observations; startup time, peak memory, and steady-state benefits must be
remeasured for this port. See the [cookbook](../cookbook/moss_tts.md) for opt-outs.

## Historical evaluation protocol

The evaluator used one H100 80 GB HBM3 GPU, 16 physical CPU cores, and 128 GiB
host memory, with PyTorch 2.13.0+cu130, SGLang 0.5.20, and Transformers 5.12.1.
The model was `OpenMOSS-Team/MOSS-TTS-v1.5` at revision
`cdd3b911b1585e3f2dbc7775ef10f9926f58850a`. The full SeedTTS English split
contained 1,088 requests at dataset revision
`27f4c1adee83b5b29b7c4b375f6b976324bda308`.

Each mode ran three repetitions with seeds 42, 43, and 44. Each repetition used
a fresh server and empty compile cache, 16 excluded warm-up requests, client
concurrency 16, maximum running requests 64, CUDA graph maximum batch size 64,
and a 2,048-token generation cap. References used the `references` format and
duration used `--token-count auto`. Non-streaming repetitions ran before
streaming repetitions. Qwen3-ASR-1.7B scored the generated audio in a separate
process (ASR concurrency 32, 64 warm-up examples).

All 6,528 generated clips were scored, with zero failed or skipped requests.
Aggregate metrics are arithmetic means of the three per-repetition metrics,
including corpus WER. Percentiles below are means of repetition percentiles,
not percentiles pooled over all requests. The evaluation accepted all 27 gates.

## Historical results

These comparisons use the initial baseline B0. The final submission improved
non-streaming QPS by **1.8628×** against B0 and **1.0639×** against the previously
promoted generation 4. The latter was the evaluator's immediate comparison.

| Metric | B0 non-streaming | Agent 6 non-streaming | B0 streaming | Agent 6 streaming |
|---|---:|---:|---:|---:|
| Requests/s | 7.7273 | 14.3947 | 2.4383 | 9.9820 |
| Audio seconds/s | 34.6237 | 64.4953 | 10.9230 | 44.7230 |
| Mean request latency (s) | 2.0617 | 1.1060 | 6.5273 | 1.5960 |
| p95 request latency (s) | 2.6090 | 1.3827 | 7.3517 | 1.9960 |
| Mean real-time factor | 0.4745 | 0.2555 | 1.5380 | 0.3684 |
| Mean time to first audio (s) | — | — | 5.3332 | 0.7164 |
| p95 time to first audio (s) | — | — | 6.0983 | 0.8407 |
| Corpus WER (%) | 1.7360 | 1.7974 | 1.8505 | 1.8281 |

| Seed | Non-streaming requests/s | Non-streaming WER (%) | Streaming requests/s | Streaming WER (%) |
|---|---:|---:|---:|---:|
| 42 | 14.432 | 2.2607 | 9.994 | 2.2105 |
| 43 | 14.385 | 1.4569 | 9.965 | 1.5239 |
| 44 | 14.367 | 1.6746 | 9.987 | 1.7500 |

The 2% WER gate applied to each mode's three-run mean. Both seed-42 repetitions
exceeded 2% individually. Non-streaming mean WER increased by 0.0614 percentage
points relative to B0. WER alone does not establish speaker similarity or
perceptual equivalence. These Qwen3-ASR numbers are not directly comparable to
the cookbook's Whisper/FunASR reference results.

## Earlier validation of the port

Local checks used Python 3.12, PyTorch 2.13.0+cu130, SGLang 0.5.21,
Transformers 5.12.1, and an H100 NVL for the targeted CUDA suite:

| Check | Result |
|---|---|
| MOSS-TTS unit suite, excluding accelerator-marked tests | 320 passed, 4 skipped, 91 deselected |
| Embedding, sampling-graph, and vocoder test files on H100 NVL | 93 passed |
| Shared async-decode and model-runner hook suites | 73 passed, 3 skipped |
| `pre-commit run --all-files` | Passed (including Rust formatting) |
| `git diff --check` | Passed |

Commands, from the repository root with its dependencies installed:

```bash
CUDA_VISIBLE_DEVICES='' python -m pytest tests/unit_test/moss_tts -q -m 'not accelerator'
python -m pytest tests/unit_test/moss_tts/test_input_embeddings.py tests/unit_test/moss_tts/test_sampling_cuda_graph.py tests/unit_test/moss_tts/test_vocoder.py -q
CUDA_VISIBLE_DEVICES='' python -m pytest tests/unit_test/pipeline/test_async_decode.py tests/unit_test/model_runner/test_base_hooks.py -q
pre-commit run --all-files
```

The unit tests exercise ordered embedding sums and storage changes, mixed
sampling across text/audio boundaries and tied logits, lookahead cancellation
and retraction bookkeeping, pinned upload reuse, and graph-owned vocoder inputs.
They also retain the existing multi-segment eager routing tests.

The current-main qualification above supplies full-model throughput, WER, speaker
similarity, startup and sampled peak-memory evidence. Listening tests and other
concurrency/hardware settings remain unmeasured. Unit tests with synthetic logits
and a small decoder do not replace full-model qualification.
