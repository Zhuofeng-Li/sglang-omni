# Fish S2 Pro runtime research

This port recovers the retained **C39 / agent-10** research candidate. The results below measure the original complete candidate, not the current upstream port or an isolated component.

## Runtime changes

- Encode reference code indices without running the quantizer's unused reconstruction path. Full quantizer forward remains available for training and calls with extra arguments.
- Reuse private CPU Snake activation temporaries. On AVX2/AVX512, place eligible activations directly in their adjacent convolution's padded input storage; version, shape, gradient and hook checks retain the normal convolution fallback.
- Skip zero-width convolution padding, retain waveform tensors in typed transport and return packed waveform bytes instead of Python sample lists.
- Allow two CPU shares per preprocessing worker, capped at eight intra-op threads, while respecting an explicit OMP override and the current CPU-plan distinction. On glibc, raise the process allocator mmap threshold to 64 MiB so large CPU temporaries can be reused. This allocator setting affects the preprocessing process, not just one tensor.

The port retains the current shared streaming-vocoder implementation and current CPU-affinity policy. It does not restore the older scheduler from the snapshot.

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

## Evidence and limits

[Frozen accepted metrics](https://github.com/OpenRSI-Foundation/sglang-omni-fish-s2-pro-runtime-d154/blob/main/recovery/radix-20261010/latest/rolling-current.json), [pristine baseline](https://github.com/OpenRSI-Foundation/sglang-omni-fish-s2-pro-runtime-d154/blob/main/recovery/radix-20261010/latest/baseline.json), [complete Judge output](https://github.com/OpenRSI-Foundation/sglang-omni-fish-s2-pro-runtime-d154/blob/main/logs/runs/185b0e62f4b34e518f85f587fc17c67e/sglang-omni-fish-s2-pro-runtime/submissions/agent-10/test_output.txt), and [research snapshot](https://github.com/OpenRSI-Foundation/sglang-omni-fish-s2-pro-runtime-d154/blob/main/recovery/radix-20261010/latest/workspace.tar.gz). The evidence repository requires access; the tables above are self-contained.

Later C45 work did not replace the scored C39 candidate. The CPU activation fast path is conditional; other architectures retain the normal padding path. The new port has not been measured on the original x86/H200 setup.

The port targets upstream `fa4e6d1f1b4c962ecc223e1422f6e879f5ce1141` and preserves newer runtime changes. Current-port CPU tests and full pre-commit checks are reported in the PR. No new GPU benchmark, multilingual qualification or low-concurrency result is claimed. Graph capture adds startup work and resident memory where used.
