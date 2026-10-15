# Qwen3-TTS Base runtime research

This port recovers the Qwen3-TTS Base 1.7B candidate evaluated in OpenRSI
submission 6 and the Base 0.6B candidate evaluated in submission 10. The historical complete candidates improved non-streaming
concurrency-16 throughput by **44.36% (0.6B)** and **26.15% (1.7B)**;
streaming throughput improved by **7.17%** and **6.20%**, respectively.
These measurements use the historical source and are not a new benchmark of
the current upstream port, or an isolated measurement of any one component.
The paired current-port measurements below separately cover both checkpoint
sizes, including quality, startup time and resident GPU memory.

## Runtime changes

- Base cloning requests use the existing full prefill graph backend, with
  token buckets through 1,024 for 1.7B and the 8,192-token prefill budget for 0.6B. CustomVoice retains its existing 512-token
  ladder; VoiceDesign and unknown variants keep the breakable default.
- For 1.7B, whole-utterance CUDA vocoding reuses exact frame/batch graphs for 1–256
  frames and 1–4 requests. Missing shapes, larger batches, deterministic
  decoding and disabled graphs use the original tokenizer path. No graph
  bucket padding substitutes for an exact batch shape.
- For 0.6B, whole-utterance CUDA vocoding preserves the native chunk/context
  boundaries (300/25 codec frames), captures exact chunk shapes for one or two
  requests and uses a dedicated stream. Default non-streaming vocoder batching
  becomes two requests with no collection wait; explicit overrides win.
  Whole-utterance graphs require a recognized Base checkpoint size.
- Capture larger shapes first within a shared graph pool to limit reserved
  memory fragmentation. This adds startup work and resident graph memory.
- The initial incremental decoder launches its next cohort before resolving
  the previous one, retaining at most two in flight. Existing tail-decode
  routing, invalid-row handling and cancellation ownership remain in use.
- Fence each codec arena host index slot's outstanding upload before ring
  reuse. The four-slot ring and index values are unchanged.

Upstream already contains the historical invalid-row-mask transport mechanism
in [#2548](https://github.com/sgl-project/sglang-omni/pull/2548). This port uses
that implementation. It also preserves the follow-up scheduling in
[#2400](https://github.com/sgl-project/sglang-omni/pull/2400) and the first-chunk
tail runner in [#2658](https://github.com/sgl-project/sglang-omni/pull/2658).

## Exact frame shapes and capture cost

The 1.7B ladder captures 256 frame lengths for four batch sizes: up to 1,024
whole-utterance graphs. This is an intentional startup tradeoff, not a claim
that length bucketing is impossible. The measured warm-cache startup cost
below increases from 138.569 to 306.147 seconds; streaming throughput is
nearly unchanged in that single pair.

For a native batch whose longest sequence is N frames, the tokenizer pads
shorter requests to N, decodes that batch, and trims each waveform to its
original length. The graph path preserves those same frame and batch shapes.
All captured 1.7B lengths are below the tokenizer's 300-frame chunk boundary,
so the graph replaces exactly one native decoder call.

Padding N to a larger bucket would change the decoder's tensor shapes. The
causal decoder makes prefix-preserving bucketing plausible, but that alone
does not establish bitwise equality: attention and convolution kernels can
have shape-dependent floating-point behavior. Trimming the extra output
samples does not establish equality of the retained samples. Exact shapes
therefore retain the currently validated contract; they are not asserted to
be mathematically necessary. No exact-versus-bucketed experiment has been run,
so this PR does not claim that 1,024 captures are the best cost/performance
choice or that buckets would lose the throughput gain.

A bucketed policy needs a real-tokenizer comparison across lengths on both
sides of each bucket boundary, mixed-length batches, reference trimming and
fallback paths, followed by startup/memory and paired serving measurements.
It must also preserve the 0.6B tokenizer's separate 300/25-frame chunk/context
policy. For startup-sensitive deployments, disabling the existing
`initial_cuda_graph` option also disables these whole-utterance graphs and
keeps the tokenizer fallback; it also disables initial streaming graphs.

## Paired current-port measurements (2026-10-14)

Both revisions ran sequentially on the same allocated NVIDIA H200
(143,771 MiB, driver 595.71.05). Base is the original branch point
`fa4e6d1f1b4c962ecc223e1422f6e879f5ce1141`; the measured PR head is
`8becbc36f1fd78b1c3cd99d1b075201326b4e240`. This comparison does not use a
moving `main`. Both source trees were clean, and all clients and scorers ran
from the unchanged base checkout.

Server and client affinity was CPU 0–15: 16 physical cores on the GPU-local
NUMA node. Those CPUs were not exclusively reserved, and no 128 GiB host-memory
cap was imposed for this follow-up. The container image was
`docker.io/hongccc/sglang-omni@sha256:ebe4239e29a764ee3a2806385c061c5fd438a26f01458e503d3822dcba5790df`,
with SGLang upgraded to 0.5.21 as required by this checkout, Python 3.12,
PyTorch 2.13.0+cu130 and Transformers 5.12.1.

Each of the eight cohorts used the full 1,088-request SeedTTS EN split in
native order, concurrency 16, seed 42 and a 2,048-token cap. A fresh server
was started for each mode. Sixteen requests using the first reference were
excluded as warmup; normal reference caching and default KV-cache sizing
were retained. Weights were already downloaded. These are single runs,
not three-seed means or estimates with confidence intervals.

### Throughput and quality

WER is the full corpus edit-count ratio, including outliers. SIM is mean
WavLM cosine similarity multiplied by 100, not a percentage of passing
samples. Each row's base and head generated 1,088 successful requests, and
each WER/SIM calculation covered those same 1,088 IDs with zero failures or
skips. The corpus WER and SIM mean were independently recomputed from the
per-sample records.

| Model | Mode (C16) | Base requests/s | Head requests/s | Change | Base WER (%) | Head WER (%) | Base SIM | Head SIM |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 0.6B | Non-streaming | 21.058 | 31.580 | +49.97% | 1.8923 | 1.3816 | 70.1584 | 70.0585 |
| 0.6B | Streaming | 27.073 | 35.671 | +31.76% | 1.5323 | 1.1639 | 70.3511 | 70.4384 |
| 1.7B | Non-streaming | 24.430 | 30.245 | +23.80% | 0.9462 | 1.1387 | 71.5595 | 71.4940 |
| 1.7B | Streaming | 32.223 | 32.459 | +0.73% | 1.1304 | 1.2560 | 71.5773 | 71.1164 |

The 1.7B WER increased by 0.1926 percentage points in non-streaming and
0.1256 points in streaming. Its streaming throughput difference is small,
and its SIM decreased by 0.4609 points. These observations do not establish
quality equivalence or a repeatable streaming speedup.

| Model | Mode | Base/head max-token hits | Base/head samples with WER >50% |
| --- | --- | ---: | ---: |
| 0.6B | Non-streaming | 1 / 3 | 2 / 2 |
| 0.6B | Streaming | 1 / 0 | 1 / 0 |
| 1.7B | Non-streaming | 0 / 0 | 0 / 1 |
| 1.7B | Streaming | 0 / 1 | 1 / 1 |

No capped or high-WER sample was dropped. SIM used batch size 1 for every
cohort with complete waveforms and the same scorer. The initial batch-8
attempt exhausted memory while padding long 0.6B baseline outputs, including
a 163.84-second sample; batch size was reduced uniformly without changing
audio, scoring models or thresholds.

### Startup and resident memory

Startup is process spawn to the first healthy HTTP response, measured before
the 16 excluded warmups. The second successful launch of each revision
(streaming mode) provides the warm-cache comparison: compiler caches were
warm, but each new process still captured its CUDA graphs.

| Model | Base startup (s) | Head startup (s) | Additional time (s) |
| --- | ---: | ---: | ---: |
| 0.6B | 179.079 | 248.180 | 69.101 |
| 1.7B | 138.569 | 306.147 | 167.577 |

The preceding non-streaming launches took 329.675/243.170 seconds
(base/head, 0.6B) and 154.100/349.664 seconds (1.7B). The first 0.6B base
launch had cold compiler caches, so its longer time is not evidence that
this PR reduces startup time. Each timing is one observation.

Resident memory below is serving-process `nvidia-smi used_gpu_memory` after
the 16 excluded warmup requests, rather than a peak or an isolated graph
allocation measurement.

| Model | Mode | Base resident memory (MiB) | Head resident memory (MiB) |
| --- | --- | ---: | ---: |
| 0.6B | Non-streaming | 126068 | 124386 |
| 0.6B | Streaming | 123430 | 124390 |
| 1.7B | Non-streaming | 126494 | 127638 |
| 1.7B | Streaming | 123514 | 124676 |

Default automatic KV-cache sizing was retained, so total resident memory
mixes weights, KV cache, graphs and allocator reservations. A lower total
does not imply that graph capture is free. These measurements do not
qualify the graph ladders for smaller GPUs.

### Reproduction

Pinned inputs:

| Input | Revision or SHA-256 |
| --- | --- |
| `Qwen/Qwen3-TTS-12Hz-0.6B-Base` | `5d83992436eae1d760afd27aff78a71d676296fc` |
| `Qwen/Qwen3-TTS-12Hz-1.7B-Base` | `fd4b254389122332181a7c3db7f27e918eec64e3` |
| `zhaochenyang20/seed-tts-eval-arrow` (EN) | `27f4c1adee83b5b29b7c4b375f6b976324bda308` |
| `Qwen/Qwen3-ASR-1.7B` | `7278e1e70fe206f11671096ffdd38061171dd6e5` |
| SIM `wavlm_large_finetune.pth` | `51f07e3b94d9e0262a6a675ef5a087be3dd09e8c62e9d886827f44f82fe7f94b` |
| SIM `wavlm_large.pt` | `6fb4b3c3e6aa567f0a997b30855859cb81528ee8078802af439f7b2da0bf100f` |

The unchanged benchmark loader pins the dataset revision above. Set
`MODEL_PATH` and `ASR_PATH` to the local snapshots of the listed revisions,
`MODEL_ID` to the checkpoint ID, `OUT` to a separate directory per cohort,
and `PORT` to an unused port. Use `qwen3_tts_0_6b.yaml` or
`qwen3_tts_1_7b.yaml` as `CONFIG`. Run the server from the selected base/head
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

## Historical 1.7B experiment identity

The work was developed by an autonomous research agent using
[RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness),
from [OpenRSI proposal #154](https://github.com/OpenRSI-Foundation/OpenRSI-Index/discussions/154).

- Initial source: `1523543056bf334bc2f4d69db23aad0a002cedf2`.
- Research run: `51d85322a9484e83bcf8242a5c020dad`, submission `agent-6`.
- Evaluated source inventory SHA-256:
  `228108a4b3e11d9e81ecfd109cb504921e732a711f98e77717f070c5f9842279`.
- Checkpoint: `Qwen/Qwen3-TTS-12Hz-1.7B-Base`, revision
  `fd4b254389122332181a7c3db7f27e918eec64e3`.
- Dataset: full SeedTTS EN, 1,088 requests, revision
  `27f4c1adee83b5b29b7c4b375f6b976324bda308`, in native order.
- One NVIDIA H200, 16 physical CPU cores on one NUMA node, 128 GiB host
  memory. SGLang 0.5.20, PyTorch 2.13.0+cu130.
- Non-streaming and streaming at concurrency 16, each using seeds 42/43/44;
  16 TTS warmups per run excluded from scoring. Native engine admission and
  decode graph limits remain 64/64; the maximum token cap is 2,048.
- Stock diagnostic ASR followed by independent original-source authoritative
  Qwen3-ASR-1.7B on the generated WAVs, concurrency 32 and 64 ASR warmups.

## Historical 1.7B complete results

Values are arithmetic means of all three per-run summaries, including latency
percentiles. They are not percentiles pooled across runs. Baseline refers to
the initial pristine version, rather than the preceding accepted candidate.

| Mode | Metric | Pristine | Submission 6 |
| --- | --- | ---: | ---: |
| Non-streaming C16 | Requests/s | 21.1670 | 26.7017 (+26.15%) |
| Non-streaming C16 | Mean full latency (s) | 0.7530 | 0.5950 |
| Non-streaming C16 | p99 full latency (s) | 1.5030 | 0.9927 |
| Non-streaming C16 | p99 RTF | 0.4231 | 0.1780 |
| Non-streaming C16 | Corpus WER (%) | 1.0243 | 1.0383 |
| Streaming C16 | Requests/s | 22.7613 | 24.1733 (+6.20%) |
| Streaming C16 | Mean first audio (ms) | 89.87 | 75.13 |
| Streaming C16 | p95 first audio (ms) | 127.00 | 114.57 |
| Streaming C16 | p99 first audio (ms) | 997.63 | 252.80 |
| Streaming C16 | Mean full latency (s) | 0.6997 | 0.6593 |
| Streaming C16 | p99 full latency (s) | 1.4773 | 1.0790 |
| Streaming C16 | p99 RTF | 0.3554 | 0.2006 |
| Streaming C16 | Corpus WER (%) | 1.0466 | 1.0438 |
| Streaming C16 | C50 (%) | 99.85 | 99.91 |

All prescribed throughput repetitions:

| Mode | Seed | Pristine requests/s | Submission 6 requests/s |
| --- | ---: | ---: | ---: |
| Non-streaming C16 | 42 | 21.246 | 26.707 |
| Non-streaming C16 | 43 | 21.116 | 26.774 |
| Non-streaming C16 | 44 | 21.139 | 26.624 |
| Streaming C16 | 42 | 23.035 | 24.313 |
| Streaming C16 | 43 | 22.565 | 24.190 |
| Streaming C16 | 44 | 22.684 | 24.017 |

The complete candidate passed all 27 prescribed quality/performance gates,
resource and cleanup checks. All 6,528 scored TTS requests and 96 TTS warmups
completed with no failures or skips. Maximum observed GPU memory was
135,553 MiB. The non-streaming WER increase of 0.0140 percentage points is
retained; WER does not establish perceptual or speaker equivalence.

## Evidence and limits

[Complete Judge output](https://github.com/OpenRSI-Foundation/sglang-omni-qwen3-tts-base-1.7b-runtime-d154/blob/main/logs/runs/51d85322a9484e83bcf8242a5c020dad/sglang-omni-qwen3-tts-base-1.7b-runtime/submissions/agent-6/test_output.txt),
[frozen accepted metrics](https://github.com/OpenRSI-Foundation/sglang-omni-qwen3-tts-base-1.7b-runtime-d154/blob/main/recovery/radix-20261010/latest/rolling-current.json)
and the
[research snapshot](https://github.com/OpenRSI-Foundation/sglang-omni-qwen3-tts-base-1.7b-runtime-d154/blob/main/recovery/radix-20261010/latest/workspace.tar.gz)
retain the original feedback, hypothesis history and source diff. The evidence
repository requires access; the tables above are self-contained.

The historical experiment used a fixed public English workload and one
allocation. The separate current-port comparison above does not provide
low-concurrency, multilingual or smaller-device serving qualification. Graph capture can
increase startup time and memory use. The port also retains newer upstream
tail-decode and device abstractions, so byte identity with the historical
candidate is not claimed. Current-port regression coverage and the exact
validation environment are reported in the pull request.

## Historical 0.6B submission 10

Research run: `62937fcd31464d01b46ce685e6ca78e3`. Evaluated source inventory SHA-256: `96b563e447413d24e88a8ee9eeb75834ca2e6f4d9608c6bf66450eb9a159b1a4`.

The 0.6B experiment used the same six-run workload and hardware envelope above. Its checkpoint was Qwen/Qwen3-TTS-12Hz-0.6B-Base. All 27 gates passed, with zero scored failures or skips.

| Mode | Metric | Pristine | submission 10 |
| --- | --- | ---: | ---: |
| Non-streaming C16 | Requests/s | 21.3553 | 30.8277 (+44.36%) |
| Non-streaming C16 | Audio seconds/s | 91.8010 | 134.2343 |
| Non-streaming C16 | Mean full latency (s) | 0.7453 | 0.5150 |
| Non-streaming C16 | p99 full latency (s) | 1.6123 | 0.8643 |
| Non-streaming C16 | p99 RTF | 0.4133 | 0.1525 |
| Non-streaming C16 | Corpus WER (%) | 1.2029 | 1.2420 |
| Streaming C16 | Requests/s | 22.5917 | 24.2120 (+7.17%) |
| Streaming C16 | Audio seconds/s | 98.1717 | 106.4243 |
| Streaming C16 | Mean first audio (ms) | 93.0667 | 74.0000 |
| Streaming C16 | p95 first audio (ms) | 121.0333 | 114.1667 |
| Streaming C16 | p99 first audio (ms) | 1370.3000 | 270.0000 |
| Streaming C16 | Mean full latency (s) | 0.7040 | 0.6573 |
| Streaming C16 | p99 full latency (s) | 1.8830 | 1.0883 |
| Streaming C16 | p99 RTF | 0.4273 | 0.1965 |
| Streaming C16 | Corpus WER (%) | 1.2308 | 1.2755 |
| Streaming C16 | C50 (%) | 99.6633 | 99.9400 |

All prescribed 0.6B throughput repetitions:

| Mode | Seed | Pristine requests/s | Submission 10 requests/s |
| --- | ---: | ---: | ---: |
| Non-streaming C16 | 42 | 21.709 | 31.666 |
| Non-streaming C16 | 43 | 21.014 | 31.319 |
| Non-streaming C16 | 44 | 21.343 | 29.498 |
| Streaming C16 | 42 | 22.899 | 25.217 |
| Streaming C16 | 43 | 22.759 | 24.068 |
| Streaming C16 | 44 | 22.117 | 23.351 |

[Frozen accepted metrics](https://github.com/OpenRSI-Foundation/sglang-omni-qwen3-tts-base-0.6b-runtime-d154/blob/main/recovery/radix-20261010/latest/rolling-current.json), [pristine baseline](https://github.com/OpenRSI-Foundation/sglang-omni-qwen3-tts-base-0.6b-runtime-d154/blob/main/recovery/radix-20261010/latest/baseline.json), [complete Judge output](https://github.com/OpenRSI-Foundation/sglang-omni-qwen3-tts-base-0.6b-runtime-d154/blob/main/logs/runs/62937fcd31464d01b46ce685e6ca78e3/sglang-omni-qwen3-tts-base-0.6b-runtime/submissions/agent-10/test_output.txt), and [research snapshot](https://github.com/OpenRSI-Foundation/sglang-omni-qwen3-tts-base-0.6b-runtime-d154/blob/main/recovery/radix-20261010/latest/workspace.tar.gz). The evidence repository requires access; the tables above are self-contained.

Submission 14 reached a higher non-streaming score but failed a streaming guard; the retained candidate is submission 10. Its static-input padding optimization is independently covered by [#2754](https://github.com/sgl-project/sglang-omni/pull/2754), so it is not duplicated here. The combined port also shares the 1.7B capture order and initial-cohort overlap changes. Consequently, neither historical result is a new measurement of this combined patch.
