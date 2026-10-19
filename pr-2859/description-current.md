## Changes

- Fuse compatible TP1 FP16/BF16 channel embeddings, capture default-profile mixed sampling, and use eligible async decode lookahead.
- Batch output copies and retain/fence asynchronous buffers; keep eager, graph-disabled and failed-capture fallbacks.
- Capture exact prefill lengths 1–512 and single-segment non-streaming vocoder lengths 1–128 in the default colocated layout.
- Preserve this run's OpenRSI provenance. #2780 is closed, so the earlier overlap/landing-order question is resolved.

**Changed defaults:** the colocated AR stage budget is 0.60 instead of 0.72 to reserve graph-capture headroom. Disabling dense capture alone retains 0.60; operators who disable capture can explicitly restore `stages.tts_engine.gpu_memory_fraction: 0.72`.

Additional default changes: the MOSS factory enables eligible async decode (previously off) with minimum batch size 2; the colocated configuration requests exact breakable prefill buckets 1–512 and non-streaming segment graphs 1–128. Eligibility and eager/failed-capture fallbacks remain in force. The following is an override fragment for an existing MOSS pipeline config to disable these three additions; the AR budget stays 0.60 unless explicitly changed:

```yaml
stages:
  tts_engine:
    factory:
      enable_async_decode: false
    engine:
      cuda_graph_backend_prefill: disabled
  vocoder:
    factory:
      segment_graph_max_frames: 0
```

This override has not been benchmarked as a mitigation for the c64 streaming regression. The cause remains under investigation; no result below is attributed to an individual component.

Published head: `1894fa88fa8b09392b0aa0625eec34aae3e95edd`. Prepared candidate `757c09eb272079b6c08f88bcaa393ffe3845029a` integrates the runtime with frozen main `2d5de98cd92b17df7974ac2ef4192b4a99263845` and is under qualification; it is not yet the published PR head. No doc/docs files are changed.

## Paired comparison on current main

Measured 2026-10-19: prepared candidate `757c09eb272079b6c08f88bcaa393ffe3845029a` versus frozen main `2d5de98cd92b17df7974ac2ef4192b4a99263845`, one Radix H100 80GB HBM3. **All requested c1/c64 × non-streaming/streaming generation, WER and WavLM SIM measurements are complete:** 16 cohorts, each with 1088/1088 requests completed and scored, zero failures or quality skips. All four paired blocks passed source/GPU/config/sample-order and strict ABBA checks; scorer-weight hashes were unchanged throughout scoring. Measurement coverage is complete; the c64 streaming regressions remain under investigation, so this does not establish merge readiness.

Full SeedTTS EN (1088 requests), pinned model/codec/data revisions in the evidence, 16 excluded warmups, 2048-token cap, request/decode-graph caps 64 and matched AR budget 0.60. Seeds 42/43 run main(42) → PR(42) → PR(43) → main(43), with fresh services/caches per pass. Req/s, mean latencies, corpus WER and SIM below are arithmetic means across the matched seeds; slash-separated p95 values retain seed 42/43 and are not pooled or averaged. WER is percent; SIM is cosine similarity ×100, already scaled by the scorer. First audio means the first audio payload. Each arm has 2176 scored requests per mode/concurrency. These are direct PR qualification measurements, not a new research run.

### Non-streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | N/A: EN-only workload |
| 16 | N/A: historical EN-only workload |
| 32 | N/A: outside requested EN-only backfill |
| 64 | N/A: EN-only workload |

| Concurrency | EN req/s, latency mean/p95, WER, SIM, failed/attempted |
| ---: | --- |
| 1 | Req/s **1.3135 → 1.4395 (+9.59%)**; latency mean **0.7615 → 0.6945 s**, p95 seeds **0.953/0.958 → 0.873/0.875 s**; WER **1.8295 → 1.8253%**; SIM **68.8997 → 68.8997**; failures **0/2176 → 0/2176** |
| 64 | Req/s **22.2285 → 34.6880 (+56.05%)**; latency mean **2.8155 → 1.8015 s**, p95 seeds **3.596/3.590 → 2.305/2.296 s**; WER **1.8923 → 1.9342%**; SIM **68.9359 → 68.9123**; failures **0/2176 → 0/2176** |

### Streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | N/A: EN-only workload |
| 16 | N/A: historical EN-only workload |
| 32 | N/A: outside requested EN-only backfill |
| 64 | N/A: EN-only workload |

| Concurrency | EN req/s, latency mean/p95, first audio mean/p95, WER, SIM, failed/attempted |
| ---: | --- |
| 1 | Req/s **1.2640 → 1.3485 (+6.69%)**; latency mean **0.7910 → 0.7415 s**, p95 seeds **0.993/0.991 → 0.934/0.931 s**; first audio mean **0.3419 → 0.3218 s**, p95 seeds **0.3619/0.3634 → 0.3458/0.3430 s**; WER **1.8212 → 1.8212%**; SIM **68.8967 → 68.8967**; failures **0/2176 → 0/2176** |
| 64 | Req/s **15.5695 → 14.7200 (−5.46%)**; latency mean **4.0300 → 4.3070 s**, p95 seeds **5.157/5.165 → 4.993/5.048 s**; first audio mean **2.13045 → 3.40420 s**, p95 seeds **2.4460/2.4786 → 3.9724/4.0667 s**; WER **1.8505 → 1.9007%**; SIM **68.8684 → 68.9742**; failures **0/2176 → 0/2176** |

**c64 streaming regresses in both seeds:** throughput falls while mean/full-response and first-audio latency increase, despite improved response p95. This is a measured tradeoff of the current candidate; component causality has not been established. Quality coverage is complete; regression investigation remains pending, so the PR is not merge-ready.

Current WER also changes at c64: mean corpus WER rises by **0.0419 percentage points non-streaming** and **0.0502 points streaming**. Non-streaming worsens in both seeds; streaming seed 42 is unchanged and seed 43 worsens by 0.1005 points. Seed 42 WER exceeds 2% in both arms for all four requested mode/concurrency blocks; the two-seed means are below 2%. No outliers were removed. Mean SIM is unchanged at c1; at c64 it changes by −0.0237 score points non-streaming and +0.1058 streaming. These small score changes do not resolve the observed throughput/first-audio regression.

c64 playback continuity (main → PR; values in seed 42/43 order):

| Metric | Main → PR |
| --- | --- |
| Evaluated / single-chunk N/A | 1083/1083 evaluated, 5/5 N/A → 1085/1087 evaluated, 3/1 N/A |
| Playback underrun p99 (ms) | 65.7/0 → 0/8 |
| C50 (%) | 98.80/99.45 → 99.08/99.63 |
| C100 (%) | 99.17/99.54 → 99.26/99.63 |
| C200 (%) | 99.91/99.82 → 99.72/99.63 |

The summary cannot supply a bilingual geometric mean from an EN-only benchmark. The requested backfill is explicitly narrower than a complete bilingual c1/c16/c32/c64 matrix.

Historical c16 was measured on **2026-10-16**, with main `85d4219916c5457995fc7ac3b53b7e5b5ab75ea0`, the then-integrated/repaired candidate, three repeats (42/43/44) and the same 0.60 budget in both arms. Arithmetic means of the repeats are below; full per-seed results and exact evaluated identities are archived. These are not new-head/current-main measurements.

| Metric | Main non-streaming | Candidate non-streaming | Main streaming | Candidate streaming |
| --- | ---: | ---: | ---: | ---: |
| EN req/s | 11.736 | 16.415 | 9.376 | 12.190 |
| Mean / p95 latency (s) | 1.356 / 1.713 | 0.969 / 1.212 | 1.698 / 2.134 | 1.304 / 1.632 |
| Mean / p95 first audio (s) | N/A | N/A | 0.7259 / 0.8412 | 0.6073 / 0.6976 |
| Corpus WER (%) | 1.7611 | 1.7332 | 1.8142 | 1.7249 |
| WavLM SIM (cosine ×100) | 69.0594 | 68.9953 | 68.9874 | 69.0849 |
| Failed / attempted across repeats | 0 / 3264 | 0 / 3264 | 0 / 3264 | 0 / 3264 |

Individual seed-42 WER exceeded 2% in all four historical mode/arm conditions; the three-repeat means are below 2%. Historical p95 values above are arithmetic means of per-repeat p95, not pooled percentiles. The client did not observe finish reasons, so zero token-cap hits do not prove zero truncation. No outliers were removed.

## Costs

Historical c16 startup increases by about **37 seconds**, and 10-second-sampled peak VRAM increases by about **3.7 GiB**. These costs belong to the historical source/configuration, not the prepared current-main integration.

| Historical c16 metric | Main non-streaming | Candidate non-streaming | Main streaming | Candidate streaming |
| --- | ---: | ---: | ---: | ---: |
| Startup (s) | 92.06 | 129.08 | 92.06 | 129.42 |
| Sampled peak VRAM (GiB) | 67.12 | 70.86 | 66.94 | 70.63 |

Current-integration c1 costs (main → PR; measurements from 2026-10-19):

| Metric | c1 non-streaming | c1 streaming |
| --- | --- | --- |
| Startup-to-ready, mean (s) | 114.105 → 156.642 (**+42.537**) | 113.105 → 154.640 (**+41.535**) |
| Sampled peak VRAM, both seeds (GiB) | 66.864 → 70.423 (**+3.559**) | 66.733 → 70.423 (**+3.690**) |
| Successful captures, each seed | 152 → 19,236 (**+19,084**) | 152 → 19,236 (**+19,084**) |

Startup runs from just before the server subprocess launch until health-ready, including model/graph initialization and excluding client imports, downloads and workload warmup. GPU memory is sampled every 0.5 seconds; peaks are the same across both seeds for each cell. Capture counts are unique successful capture events over the whole cohort, not live graphs after shutdown. c64 streaming costs are reported below. The increased startup, memory and capture count must be weighed against the measured throughput; quality qualification is still incomplete.

c64 non-streaming costs (main → PR; seeds 42/43, measured 2026-10-19):

| Metric | Main → PR |
| --- | --- |
| Startup-to-ready, mean (s) | 113.106 → 153.623 (**+40.518**) |
| Sampled peak VRAM, seeds 42/43 (GiB) | 67.231/67.331 → 71.028/71.054 (**+3.797/+3.723**) |
| Successful captures, each seed | 152 → 19,236 (**+19,084**) |

The same startup, memory-sampling and capture-count methods above apply. These are generation-only measurements; WER and SIM are now reported above.

c64 streaming costs (main → PR; seeds 42/43, measured 2026-10-19):

| Metric | Main → PR |
| --- | --- |
| Startup-to-ready, mean (s) | 112.601 → 152.135 (**+39.534**) |
| Sampled peak VRAM, seeds 42/43 (GiB) | 67.271/67.315 → 70.823/70.862 (**+3.553/+3.547**) |
| Successful captures, each seed | 152 → 19,236 (**+19,084**) |

The same measurement methods above apply. c64 streaming incurs these costs alongside the observed throughput/first-audio regressions; WER and SIM are now measured and reported above.

## Tests

- Current-integration main and candidate c1 smoke succeeded. The first candidate attempt encountered a port-bind conflict; the retry uses independent ports and retains the failed attempt.
- Current integrated MOSS regression suite passed **365 cases** on the assigned H100 before full generation. All c1 generation cohorts passed full request-count, zero-failure, ABBA-order, source/GPU/config and sample-order checks; c64 generation is running. WER/SIM and complete c64 streaming costs are reported below. The measured integration also passed the full pre-commit suite with its worktree unchanged. Historical repaired-source counts belong to their original revision.
- Published-head CI is green, including non-streaming, streaming, consistency and stress in [Omni CI](https://github.com/sgl-project/sglang-omni/actions/runs/39045568536). The preset is MOSS LocalTransformer, so it does not replace dedicated Delay qualification. CI for a subsequently published integration will be checked separately.
- A same-candidate async-decode on/off isolation is now running after the completed primary SIM pass: c64 streaming, full 1088 EN, seeds 42/43 in ABBA order, matched 0.60 budget and full WER/SIM. It changes only the factory toggle, preserves the measured candidate and all original results, and is not a standalone PR/main gain. Its first generation pass has started; no ablation result is claimed yet.
- Primary requested measurement coverage is complete. Streaming-regression diagnosis, CI for a subsequently published integration, independent reviewer approval and the MOSS-team notice mentioned by the reviewer remain pending; this PR is not represented as merge-ready.

Developed by an autonomous research agent using [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) in [OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index), with co-author [Kangda Wei (@WeiKangda)](https://github.com/WeiKangda); [qualification and historical evidence](https://github.com/Zhuofeng-Li/sglang-omni/tree/codex/omni-review-evidence-20261019/pr-2859).
