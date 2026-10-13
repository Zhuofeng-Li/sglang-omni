# MOSS-TTS v1.5 runtime research

This port recovers the retained **H12 / agent-10** research candidate. The results below measure the original complete candidate, not the current upstream port or an isolated component.

## Runtime changes

- Enable the existing breakable prefill backend and asynchronous decode scheduler.
- Gate lookahead to compatible non-streaming audio batches. Preserve per-launch rows, feedback embeddings and delay state until resolve; restore committed state for finished or retracted requests.
- Upload non-streaming sampling metadata together, retain one owned output/embedding copy per batch and capture the feedback embedding alongside the sampling graph. Streaming and unsupported sampling profiles retain their synchronous paths.
- Reuse codec-attention cumulative-length metadata instead of allocating it on every layer invocation.

Current upstream already owns reference encoding in the model-local reference encoder with a dedicated CUDA stream. This port keeps that implementation instead of restoring the snapshot's older encoder service in stages.py. The existing same-dtype input-embedding accumulator is also retained.

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

The port targets upstream `fa4e6d1f1b4c962ecc223e1422f6e879f5ce1141` and preserves newer runtime changes. Current-port CPU tests and full pre-commit checks are reported in the PR. No new GPU benchmark, multilingual qualification or low-concurrency result is claimed. Graph capture adds startup work and resident memory where used.
