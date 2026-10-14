# MOSS-TTS v1.5 runtime research

This port recovers the retained **H12 / agent-10** research candidate. The historical results measure the original complete candidate. A separate paired current-port experiment below measures the complete upstream port, not an isolated component.

## Runtime changes

- Enable the existing breakable prefill backend and asynchronous decode scheduler.
- Gate lookahead to compatible non-streaming audio batches. Preserve per-launch rows, feedback embeddings and delay state until resolve; restore committed state for finished or retracted requests.
- Upload non-streaming sampling metadata together, retain one owned output/embedding copy per batch and capture the feedback embedding alongside the sampling graph. Streaming and unsupported sampling profiles retain their synchronous paths.
- Reuse codec-attention cumulative-length metadata instead of allocating it on every layer invocation.

Current upstream already owns reference encoding in the model-local reference encoder with a dedicated CUDA stream. This port keeps that implementation instead of restoring the snapshot's older encoder service in stages.py. The existing same-dtype input-embedding accumulator is also retained.

## Paired current-port measurements (2026-10-14)

This experiment exercises MOSS **Delay** with `moss_tts.yaml`, including
reference cloning and streaming, rather than the LocalTransformer model
selected by the `run-moss` CI suite. Base is the original branch point
`fa4e6d1f1b4c962ecc223e1422f6e879f5ce1141`; measured PR head is
`cc39d5f11d0bd96ccf018f0b66c8e6bb0c2415d8`. Both source trees were clean,
and all clients and scorers ran from the unchanged base checkout.

Both revisions ran sequentially on the same allocated NVIDIA H200
(143,771 MiB, driver 595.71.05). Server and client affinity was CPU 0–15:
16 physical cores on the GPU-local NUMA node, without exclusive CPU
reservation or a 128 GiB host-memory cap. The container image was
`docker.io/hongccc/sglang-omni@sha256:ebe4239e29a764ee3a2806385c061c5fd438a26f01458e503d3822dcba5790df`,
with SGLang upgraded to 0.5.21 as required by the checkout, Python 3.12,
PyTorch 2.13.0+cu130 and Transformers 5.12.1.

Each cohort used the full 1,088-request SeedTTS EN split in native order,
concurrency 16, seed 42 and a 2,048-token cap. Each mode started a fresh
server and excluded 16 warmup requests using the first reference. Weights
were already downloaded; normal caching and default engine settings were
retained. These are single observations, separate from the historical
three-seed means below.

### Throughput and quality

| Mode (C16) | Base requests/s | Head requests/s | Change | Base WER (%) | Head WER (%) | Base SIM | Head SIM |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Non-streaming | 10.931 | 13.264 | +21.34% | 2.2272 | 2.5119 | 68.8218 | 68.9896 |
| Streaming | 3.736 | 3.885 | +3.99% | 2.1603 | 2.3026 | 65.4231 | 65.3912 |

WER is the full corpus edit-count ratio, including all outliers. SIM is the
mean WavLM cosine similarity multiplied by 100. All four cohorts contain
1,088 successful generated requests and matching WER/SIM records, with
zero failures, skips or max-token hits. The corpus WER and SIM mean were
independently recomputed from the complete per-sample records. SIM used
batch size 1 uniformly with full waveforms and unchanged scoring models.

WER increased by 0.2847 percentage points for non-streaming and 0.1423
points for streaming. **Both base and head exceed the historical 2% WER
admission cap in this follow-up.** These data are not a new pass of those
historical gates, nor evidence of quality equivalence. The head has 11/12
samples with WER >50% (non-streaming/streaming), versus 12/9 at base; all
remain included. Streaming SIM decreased by 0.0320 points. Single runs do
not establish statistical significance, and the 21.34% non-streaming gain
must not be presented as a streaming result.

### Reproduction

Pinned inputs:

| Input | Revision or SHA-256 |
| --- | --- |
| `OpenMOSS-Team/MOSS-TTS-v1.5` | `cdd3b911b1585e3f2dbc7775ef10f9926f58850a` |
| `OpenMOSS-Team/MOSS-Audio-Tokenizer` | `3cd226ba2947efa357ef453bcad111b6eafba782` |
| `zhaochenyang20/seed-tts-eval-arrow` (EN) | `27f4c1adee83b5b29b7c4b375f6b976324bda308` |
| `Qwen/Qwen3-ASR-1.7B` | `7278e1e70fe206f11671096ffdd38061171dd6e5` |
| SIM `wavlm_large_finetune.pth` | `51f07e3b94d9e0262a6a675ef5a087be3dd09e8c62e9d886827f44f82fe7f94b` |
| SIM `wavlm_large.pt` | `6fb4b3c3e6aa567f0a997b30855859cb81528ee8078802af439f7b2da0bf100f` |

Before serving, the nine Python files in the two fixed MOSS snapshots were
materialized from cache symlinks into regular files, with SHA-256 identical
before and after. Transformers 5.12.1 otherwise resolved relative Python
imports under the cache blobs directory. No model source or weight bytes
were changed. The server log confirmed the pinned audio-tokenizer revision.

The unchanged benchmark loader pins the dataset revision above. Set
`MODEL_PATH` and `ASR_PATH` to the local snapshots of the listed revisions,
`MODEL_ID` to the checkpoint ID, `OUT` to a separate directory per cohort,
and `PORT` to an unused port. Use `moss_tts.yaml` as `CONFIG`. Run the server from the selected base/head
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
  --lang en --concurrency 16 --port "$PORT" --seed 42 --max-new-tokens 2048
  --ref-format references --token-count auto)
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

Research run: `c6d156895bb2425789d2d6516359a063`. Evaluated source inventory SHA-256: `3ccf22bb5d346e51fa1961e418304b97da71fc149ba8051216e801a40db94cca`.

The original complete candidate was evaluated on one NVIDIA H200 with 16 physical CPU cores on one NUMA node and 128 GiB host memory, using SGLang 0.5.20 and PyTorch 2.13.0+cu130. Initial runtime source: `1523543056bf334bc2f4d69db23aad0a002cedf2`.

The workload was the full SeedTTS EN set (1,088 requests, dataset revision `27f4c1adee83b5b29b7c4b375f6b976324bda308`), native order, concurrency 16, streaming and non-streaming, each with seeds 42/43/44. Six runs contain 6,528 scored requests plus 96 excluded TTS warmups. Engine admission/decode caps were 64/64 and the token cap was 2,048. Independent original-source Qwen3-ASR-1.7B scored the generated WAVs after diagnostic ASR.

All 27 prescribed performance/quality gates passed, with zero scored failures or skips. WER admission used a 2% absolute cap; other performance gates allowed 3% tolerance against the preceding accepted candidate. The gain reported here is against the initial pristine baseline. Values, including percentiles, are arithmetic means of three per-run summaries, not pooled percentiles. WER does not establish perceptual or speaker equivalence.

## Historical results

| Mode | Metric | Pristine | H12 / agent-10 |
| --- | --- | ---: | ---: |
| Non-streaming C16 | Requests/s | 10.7063 | 13.2777 (+24.02%) |
| Non-streaming C16 | Audio seconds/s | 47.9593 | 59.4810 |
| Non-streaming C16 | Mean full latency (s) | 1.4880 | 1.1990 |
| Non-streaming C16 | p99 full latency (s) | 2.1260 | 1.7350 |
| Non-streaming C16 | p99 RTF | 0.4976 | 0.3992 |
| Non-streaming C16 | Corpus WER (%) | 1.7249 | 1.8644 |
| Streaming C16 | Requests/s | 3.7063 | 3.8197 (+3.06%) |
| Streaming C16 | Audio seconds/s | 16.6070 | 17.1127 |
| Streaming C16 | Mean first audio (ms) | 3294.6000 | 3222.7333 |
| Streaming C16 | p95 first audio (ms) | 3799.2667 | 3706.0667 |
| Streaming C16 | p99 first audio (ms) | 3948.6000 | 3908.9667 |
| Streaming C16 | Mean full latency (s) | 4.2870 | 4.1667 |
| Streaming C16 | p99 full latency (s) | 5.1527 | 5.0430 |
| Streaming C16 | p99 RTF | 1.5651 | 1.5288 |
| Streaming C16 | Corpus WER (%) | 1.7277 | 1.9816 |
| Streaming C16 | C50 (%) | 43.1967 | 50.4600 |

## All prescribed throughput repetitions

| Mode | Seed | Pristine requests/s | Retained candidate requests/s |
| --- | ---: | ---: | ---: |
| Non-streaming C16 | 42 | 10.817 | 13.248 |
| Non-streaming C16 | 43 | 10.599 | 13.358 |
| Non-streaming C16 | 44 | 10.703 | 13.227 |
| Streaming C16 | 42 | 3.730 | 3.825 |
| Streaming C16 | 43 | 3.750 | 3.776 |
| Streaming C16 | 44 | 3.639 | 3.858 |

## Evidence and limits

[Frozen accepted metrics](https://github.com/OpenRSI-Foundation/sglang-omni-moss-v1.5-runtime-d154/blob/main/recovery/radix-20261010/latest/rolling-current.json), [pristine baseline](https://github.com/OpenRSI-Foundation/sglang-omni-moss-v1.5-runtime-d154/blob/main/recovery/radix-20261010/latest/baseline.json), [complete Judge output](https://github.com/OpenRSI-Foundation/sglang-omni-moss-v1.5-runtime-d154/blob/main/logs/runs/c6d156895bb2425789d2d6516359a063/sglang-omni-moss-v1.5-runtime/submissions/agent-10/test_output.txt), and [research snapshot](https://github.com/OpenRSI-Foundation/sglang-omni-moss-v1.5-runtime-d154/blob/main/recovery/radix-20261010/latest/workspace.tar.gz). The evidence repository requires access; the tables above are self-contained.

The streaming WER mean increased from 1.7277% to 1.9816%, close to the 2% admission cap. The streaming throughput gain is only 3.06%; the 24.02% non-streaming gain must not be presented as a streaming result. Later H20 trials were not eligible and H12 was restored.

The port targets upstream `fa4e6d1f1b4c962ecc223e1422f6e879f5ce1141` and preserves newer runtime changes. Current-port CPU tests and full pre-commit checks are reported in the PR. The paired H200 measurements above cover SeedTTS EN at C16; multilingual and low-concurrency behavior remains unqualified. Graph capture adds startup work and resident memory where used.
