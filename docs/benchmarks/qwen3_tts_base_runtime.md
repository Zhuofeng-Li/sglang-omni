# Qwen3-TTS Base runtime research

This port recovers the Qwen3-TTS Base 1.7B candidate evaluated in OpenRSI
submission 6 and the Base 0.6B candidate evaluated in submission 10. The historical complete candidates improved non-streaming
concurrency-16 throughput by **44.36% (0.6B)** and **26.15% (1.7B)**;
streaming throughput improved by **7.17%** and **6.20%**, respectively.
These measurements use the historical source and are not a new benchmark of
the current upstream port, or an isolated measurement of any one component.

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
allocation. It provides no current-port GPU measurement, low-concurrency,
multilingual or smaller-device serving qualification. Graph capture can
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

[Frozen accepted metrics](https://github.com/OpenRSI-Foundation/sglang-omni-qwen3-tts-base-0.6b-runtime-d154/blob/main/recovery/radix-20261010/latest/rolling-current.json), [pristine baseline](https://github.com/OpenRSI-Foundation/sglang-omni-qwen3-tts-base-0.6b-runtime-d154/blob/main/recovery/radix-20261010/latest/baseline.json), [complete Judge output](https://github.com/OpenRSI-Foundation/sglang-omni-qwen3-tts-base-0.6b-runtime-d154/blob/main/logs/runs/62937fcd31464d01b46ce685e6ca78e3/sglang-omni-qwen3-tts-base-0.6b-runtime/submissions/agent-10/test_output.txt), and [research snapshot](https://github.com/OpenRSI-Foundation/sglang-omni-qwen3-tts-base-0.6b-runtime-d154/blob/main/recovery/radix-20261010/latest/workspace.tar.gz). The evidence repository requires access; the tables above are self-contained.

Submission 14 reached a higher non-streaming score but failed a streaming guard; the retained candidate is submission 10. Its static-input padding optimization is independently covered by [#2754](https://github.com/sgl-project/sglang-omni/pull/2754), so it is not duplicated here. The combined port also shares the 1.7B capture order and initial-cohort overlap changes. Consequently, neither historical result is a new measurement of this combined patch.
