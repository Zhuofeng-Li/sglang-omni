# Fish S2 Pro runtime research

This port recovers the retained **C39 / agent-10** research candidate. The historical results measure the original complete candidate. A separate paired current-port experiment below measures the complete upstream port, not an isolated component.

## Runtime changes

- Encode reference code indices without running the quantizer's unused reconstruction path. Full quantizer forward remains available for training and calls with extra arguments.
- Retain waveform tensors in typed transport and return packed waveform bytes instead of Python sample lists, including the shared no-chunks streaming fallback.

The shipped `s2pro_tts.yaml` uses `S2ProPipelineConfig`, whose preprocessing
stage defaults to GPU 0 after #2798. No shipped Fish configuration selects CPU
preprocessing. Explicitly setting that stage's `gpu` to `null` remains supported
with upstream's unmodified encoder and thread policy.

Following review, this PR no longer changes CPU Snake activations, convolution
padding, preprocessing thread budgets or the process allocator's mmap threshold.
Those changes and their dedicated tests were removed so their CPU-only costs and
benefits can be reviewed independently. The quantizer equivalence and waveform
transport regression tests remain.

**The measurements below predate this scope reduction.** They describe the
specified complete historical revisions, including changes removed during
review, and are not a new measurement of the reduced patch. In particular,
the default-GPU pair also included the former thread policy and zero-width
padding shortcut; its speedup cannot be attributed solely to the retained
quantizer and waveform changes.

## Paired pre-split port measurements (2026-10-14)

Base is upstream `94730a87b2b3b2f8383274918c3c4ed041821ecb` after #2798;
measured head is merge `27bc65d424382d4b1e5405f89a1a57801e4c6ee1`.
Both revisions use the default GPU reference encoder, retaining upstream's
full-fp32/TF32-disabled policy, warmup, process isolation and 6 GiB reserve.
The CPU activation/padding and allocator fast paths are inactive for this
GPU preprocessing path. Both source trees were clean and ran sequentially
on the same allocated NVIDIA H200 (143,771 MiB, driver 595.71.05), using the
unchanged `94730a87` benchmark client and scorers for both revisions.

Server and client affinity was CPU 0–15: 16 physical cores on the GPU-local
NUMA node. These CPUs were not exclusively reserved; no 128 GiB host-memory
cap was imposed. `OMP_NUM_THREADS` was unset so each revision used its own
native preprocessing policy within the same affinity mask. This measures
the complete port, rather than isolating a particular optimization.

The image was
`docker.io/hongccc/sglang-omni@sha256:ebe4239e29a764ee3a2806385c061c5fd438a26f01458e503d3822dcba5790df`,
with SGLang upgraded to 0.5.21 as required by the checkout, Python 3.12,
PyTorch 2.13.0+cu130 and Transformers 5.12.1. Weights were already downloaded.

Each cohort used all 1,088 SeedTTS EN requests in native order, concurrency
16, seed 42 and a 2,048-token cap. Each mode started a fresh server and
excluded 16 warmup requests using the first reference. Normal caching and
default engine settings were retained. These are single runs on the
current port, separate from the historical three-seed results below.

### Throughput and quality

| Mode (C16) | Base requests/s | Head requests/s | Change | Base WER (%) | Head WER (%) | Base SIM | Head SIM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Non-streaming | 7.107 | 8.130 | +14.39% | 1.0215 | 1.0131 | 65.0241 | 64.9896 |
| Streaming | 7.187 | 7.317 | +1.81% | 1.0299 | 1.0550 | 64.7811 | 64.6032 |

WER uses full corpus edit counts, and SIM is mean WavLM cosine similarity
multiplied by 100. Each of the four cohorts contains 1,088 successful
requests and matching WER/SIM records, with zero failures, skips,
max-token hits or samples with WER >50%. The corpus WER and SIM mean were
independently recomputed from all per-sample records. SIM used batch size
1 uniformly with complete waveforms and identical scoring models.

Streaming WER increased by 0.0251 percentage points. SIM decreased by
0.0345 points for non-streaming and 0.1779 points for streaming. These
single-run measurements do not establish quality equivalence or
statistical significance; in particular, the 1.81% streaming throughput
change is only one paired observation. The older CPU-reference gains below
do not describe this default GPU-reference path.

| Metric | Base | Head |
| --- | ---: | ---: |
| Non-streaming mean full latency (s) | 2.241 | 1.960 |
| Streaming mean full latency (s) | 2.219 | 2.180 |
| Streaming mean first audio (s) | 1.0986 | 1.0747 |
| Streaming p99 first audio (s) | 1.4070 | 1.3640 |

### Earlier CPU-reference comparison (before merging #2798)

This separate measurement used original branch point
`fa4e6d1f1b4c962ecc223e1422f6e879f5ce1141` and pre-merge runtime
`827d97c17561d5785626a005707a6ba8e4969e13`, both with CPU reference encoding.
The same H200 allocation, CPU affinity and input/scoring protocol were used,
with the unchanged `fa4e6d1f` client. Each revision used its native CPU
preprocessing thread policy, so the complete-port comparison includes that
policy change. These values are retained for provenance, not as results
for the merged GPU-reference runtime.

| Mode (C16) | Base requests/s | Head requests/s | Change | Base WER (%) | Head WER (%) | Base SIM | Head SIM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Non-streaming | 1.496 | 3.559 | +137.90% | 1.0048 | 1.0048 | 65.0296 | 64.8667 |
| Streaming | 1.483 | 3.538 | +138.57% | 1.0466 | 1.0801 | 64.5553 | 64.5598 |

All four earlier cohorts also had 1,088 successful requests and full quality
coverage with zero skips, max-token hits or samples with WER >50%.
Streaming WER increased by 0.0335 percentage points and non-streaming SIM
fell by 0.1629 points. Mean full latency was 10.642 → 4.477 seconds for
non-streaming and 10.733 → 4.503 seconds for streaming; streaming mean/p99
first audio was 10.2555/14.7222 → 3.8409/5.8805 seconds. These single runs
are separate from both the GPU-reference comparison and the historical
three-seed experiment.

### Reproduction

Pinned inputs:

| Input | Revision or SHA-256 |
| --- | --- |
| `fishaudio/s2-pro` | `1de9996b6be38b745688de084d87a5633f714e4e` |
| `zhaochenyang20/seed-tts-eval-arrow` (EN) | `27f4c1adee83b5b29b7c4b375f6b976324bda308` |
| `Qwen/Qwen3-ASR-1.7B` | `7278e1e70fe206f11671096ffdd38061171dd6e5` |
| SIM `wavlm_large_finetune.pth` | `51f07e3b94d9e0262a6a675ef5a087be3dd09e8c62e9d886827f44f82fe7f94b` |
| SIM `wavlm_large.pt` | `6fb4b3c3e6aa567f0a997b30855859cb81528ee8078802af439f7b2da0bf100f` |

The unchanged benchmark loader pins the dataset revision above. Set
`MODEL_PATH` and `ASR_PATH` to the local snapshots of the listed revisions,
`MODEL_ID` to the checkpoint ID, `OUT` to a separate directory per cohort,
and `PORT` to an unused port. Use `s2pro_tts.yaml` as `CONFIG`. Run the server from the selected base/head
checkout, with the following environment also applied to the clients:

```bash
export CUDA_VISIBLE_DEVICES=0
export HF_HOME=/work/hf-cache
export SEEDTTS_SIM_CACHE_DIR=/work/sim-cache
export SGLANG_OMNI_TORCH_COMPILE_DEFAULT=0
export SGLANG_OMNI_STRICT_PORT=1
unset OMP_NUM_THREADS
taskset -c 0-15 python -m sglang_omni.cli serve \
  --model-path "$MODEL_PATH" --host 127.0.0.1 --port "$PORT" \
  --config "examples/configs/$CONFIG"
```

From the base checkout in another shell, wait for `/health`, then use the
same mode for both warmup and measurement (`MODE=()` for non-streaming,
`MODE=(--stream)` for streaming; Bash array syntax):

```bash
MODE=()
COMMON=(--model "$MODEL_ID" --meta zhaochenyang20/seed-tts-eval-arrow
  --lang en --concurrency 16 --port "$PORT" --seed 42 --max-new-tokens 2048)
taskset -c 0-15 python -m benchmarks.eval.benchmark_tts_seedtts \
  "${COMMON[@]}" "${MODE[@]}" --generate-only --use-existing-server \
  --max-samples 1 --warmup 15 --output-dir "$OUT/excluded-warmup"
nvidia-smi --query-compute-apps=gpu_uuid,pid,process_name,used_gpu_memory \
  --format=csv,nounits
taskset -c 0-15 python -m benchmarks.eval.benchmark_tts_seedtts \
  "${COMMON[@]}" "${MODE[@]}" --generate-only --use-existing-server \
  --max-samples 1088 --warmup 0 --fingerprint --output-dir "$OUT"
```

Stop the owned TTS server before scoring its saved WAVs. Run both scorers
from the base checkout; ASR uses the default concurrency of 32. The runtime
SIM override below leaves the repository and waveform lengths unchanged:

```bash
taskset -c 0-15 python -m benchmarks.eval.benchmark_tts_seedtts \
  "${COMMON[@]}" "${MODE[@]}" --transcribe-only --skip-gpu-cleanup \
  --asr-model-path "$ASR_PATH" --server-timeout 3600 --output-dir "$OUT"
taskset -c 0-15 python -c \
  "import runpy; import benchmarks.tasks.tts as t; t.SPEAKER_SIMILARITY_BATCH_SIZE = 1; runpy.run_module('benchmarks.eval.benchmark_tts_seedtts', run_name='__main__')" \
  "${COMMON[@]}" "${MODE[@]}" --similarity-only --device cuda:0 \
  --output-dir "$OUT"
```

Saved evidence per cohort includes command arguments, source identities,
startup/memory snapshots, `speed_results.json`, `generated.json`, and
per-sample `wer_results.json` and `similarity_results.json`. This fixed
English workload on one H200 does not establish multilingual,
low-concurrency or smaller-device behavior.

## Historical experiment

Developed with [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) under [OpenRSI proposal #154](https://github.com/OpenRSI-Foundation/OpenRSI-Index/discussions/154).

Research run: `185b0e62f4b34e518f85f587fc17c67e`. Evaluated source inventory SHA-256: `a397ed0a8c12616d841cc0d809dacc67f1da34311d46bd41d0436e8d9408af4f`.

The original complete candidate was evaluated on one NVIDIA H200 with 16 physical CPU cores on one NUMA node and 128 GiB host memory, using SGLang 0.5.20 and PyTorch 2.13.0+cu130. Initial runtime source: `1523543056bf334bc2f4d69db23aad0a002cedf2`.

The workload was the full SeedTTS EN set (1,088 requests, dataset revision `27f4c1adee83b5b29b7c4b375f6b976324bda308`), native order, concurrency 16, streaming and non-streaming, each with seeds 42/43/44. Six runs contain 6,528 scored requests plus 96 excluded TTS warmups. Engine admission/decode caps were 64/64 and the token cap was 2,048. Independent original-source Qwen3-ASR-1.7B scored the generated WAVs after diagnostic ASR.

All 27 prescribed performance/quality gates passed, with zero scored failures or skips. WER admission used a 2% absolute cap; other performance gates allowed 3% tolerance against the preceding accepted candidate. The gain reported here is against the initial pristine baseline. Values, including percentiles, are arithmetic means of three per-run summaries, not pooled percentiles. WER does not establish perceptual or speaker equivalence.

## Historical results

| Mode | Metric | Pristine | C39 / agent-10 |
| --- | --- | ---: | ---: |
| Non-streaming C16 | Requests/s | 2.6643 | 4.4980 (+68.82%) |
| Non-streaming C16 | Audio seconds/s | 10.5997 | 17.8917 |
| Non-streaming C16 | Mean full latency (s) | 5.9773 | 3.5450 |
| Non-streaming C16 | p99 full latency (s) | 8.6643 | 5.4637 |
| Non-streaming C16 | p99 RTF | 3.4023 | 1.9084 |
| Non-streaming C16 | Corpus WER (%) | 1.0243 | 1.0662 |
| Streaming C16 | Requests/s | 2.6680 | 4.3667 (+63.67%) |
| Streaming C16 | Audio seconds/s | 10.6083 | 17.3643 |
| Streaming C16 | Mean first audio (ms) | 5363.3000 | 2812.4000 |
| Streaming C16 | p95 first audio (ms) | 7048.2667 | 3862.1667 |
| Streaming C16 | p99 first audio (ms) | 7918.8000 | 4412.5667 |
| Streaming C16 | Mean full latency (s) | 5.9693 | 3.6497 |
| Streaming C16 | p99 full latency (s) | 8.6950 | 5.9030 |
| Streaming C16 | p99 RTF | 3.3729 | 1.8711 |
| Streaming C16 | Corpus WER (%) | 1.0801 | 1.0438 |
| Streaming C16 | C50 (%) | 100.0000 | 100.0000 |

## All prescribed throughput repetitions

| Mode | Seed | Pristine requests/s | Retained candidate requests/s |
| --- | ---: | ---: | ---: |
| Non-streaming C16 | 42 | 2.654 | 4.503 |
| Non-streaming C16 | 43 | 2.673 | 4.493 |
| Non-streaming C16 | 44 | 2.666 | 4.498 |
| Streaming C16 | 42 | 2.662 | 4.377 |
| Streaming C16 | 43 | 2.654 | 4.363 |
| Streaming C16 | 44 | 2.688 | 4.360 |

## Evidence and limits

[Frozen accepted metrics](https://github.com/OpenRSI-Foundation/sglang-omni-fish-s2-pro-runtime-d154/blob/main/recovery/radix-20261010/latest/rolling-current.json), [pristine baseline](https://github.com/OpenRSI-Foundation/sglang-omni-fish-s2-pro-runtime-d154/blob/main/recovery/radix-20261010/latest/baseline.json), [complete Judge output](https://github.com/OpenRSI-Foundation/sglang-omni-fish-s2-pro-runtime-d154/blob/main/logs/runs/185b0e62f4b34e518f85f587fc17c67e/sglang-omni-fish-s2-pro-runtime/submissions/agent-10/test_output.txt), and [research snapshot](https://github.com/OpenRSI-Foundation/sglang-omni-fish-s2-pro-runtime-d154/blob/main/recovery/radix-20261010/latest/workspace.tar.gz). The evidence repository requires access; the tables above are self-contained.

Later C45 work did not replace the scored C39 candidate. The CPU activation fast path is conditional; other architectures retain the normal padding path. The paired follow-up above uses the current port and a separate x86/H200 allocation; its CPU policy and runtime differ from the historical snapshot.

The port started from upstream `fa4e6d1f1b4c962ecc223e1422f6e879f5ce1141` and now includes upstream `94730a87b2b3b2f8383274918c3c4ed041821ecb`, preserving its GPU reference encoder and newer runtime changes. Current-port CPU tests and full pre-commit checks are reported in the PR. The paired H200 measurements above cover SeedTTS EN at C16; multilingual and low-concurrency behavior remains unqualified.
