Archived at 2026-10-27T03:39:35.724524+00:00. Historical body; see the live PR for current qualification.

## Changes

**Draft dependency stack on #3136.** This PR contains the Tiny increment over that prerequisite; the current stack incorporates its compatibility fixes. The measurements below compare clean upstream main with the integrated bundle, including #3136; they do not isolate this increment. The merge target must be changed to `main` after the dependency is resolved, with final integration and applicable CI verified.

- Preserve Tiny native-precision acoustic computation inside CUDA graphs, with owned timestep/rotary/projection storage and native-rounding normalization. Preserve eager and gradient paths.
- Reuse request noise storage without advancing its random generator; warm both Triton KDA prefill branches using private state before readiness.
- Capture complete Tiny AudioVAE decode at exact lengths, clone replay outputs, and fall back eagerly outside captured lengths. Dense retains the prerequisite decoder-transformer graph path.

**Changed defaults**

- Tiny CUDA/Triton KDA prefill compilation moves to startup warmup. There is no separate KDA-warmup opt-out.
- Tiny CUDA vocoding uses complete AudioVAE graphs through `min(graph_latent_steps, maximum_decode_steps)` (250 for this checkpoint). The existing configured graph limit remains 384.
- Set `stages.vocoder.factory.graph_latent_steps: 0` in a pipeline YAML to disable vocoder graph capture. Compared with the current #3136 defaults, this increment opts Tiny into GPU preprocessing with four workers, asynchronous decode, prefill graph buckets and `mps: auto`. Reference caching retains the 64 MiB cap, and Tiny has no default reference-duration cap. These Tiny settings were present in the historical measured bundle; the current prerequisite preserves conservative Tiny defaults.

## Paired comparison on current main

Current head `ea0958cb4199f7752427c6974e3c3527d96d80f3` integrates main `0fe60cf6c102caf982430e1764243c6e5c749d76`. The shared bounded worker-pool and worker-lifecycle changes affect GPU preprocessing, so fresh affected qualification is being prepared. H200 regression suites and full pre-commit passed on this integration. Latest observed main `39fbbbfed68715710917130654b115d3d514b768` adds Qwen3-Omni token-budget handling and a request-data constant, with no Ming3 runtime-path change. The tables below retain their original measured commits and do not qualify this new head.

**Historical integrated-bundle qualification: 32/32 complete, measured October 25–26, 2026 UTC. Current-head performance qualification is pending.** Clean control: upstream `58c4ebbd4a63f6bd1452346675b4d7e017b88c24`. Measured candidate: `6b871400ce1a71444049cc4a3e9d0c10bc2803d6`, integrating prerequisite head `6da60ea9669435bfdef692ccab70421eab356585`. The then-reviewed head `99c78ed53d860cb2296cf2517809fd15ddf500ad` integrated with the measured control to the tested tree `3b57222d8a32767a22e949c5c961bf12e8045dc4`. Previous head `8071abb0c80188761c99df175064fb22a5c7df0b` includes updated #3136 compatibility fixes and executable protocol stubs for CodeQL. The final commit only clarifies the cookbook; runtime files match `8cbf592f`. The historical results below are not measurements of this updated head.

Previously observed upstream was `e5af475` (October 26). Subsequent Tiny-independent and shared realtime/config changes were statically inspected; current-main performance qualification and CI remain pending. These results retain their actual measured control and are not relabeled as measurements of the later main.

One H200 (143771 MiB), identical 16-physical-core affinity/quota, 128 GiB RAM, 32 GiB shared memory, isolated fresh services/private caches. PyTorch 2.14.1+cu130, SGLang 0.5.22, Triton 3.8.0, FlashInfer 0.7.1; fixed reconstructed image and offline assets. Model `inclusionAI/Ming-3.0-tts-tiny` revision `7bd9446a8d47e462362261a0150258da6d458318`. Full Seed-TTS revision `27f4c1adee83b5b29b7c4b375f6b976324bda308`: EN 1088 and ZH 2020 requests per arm.

No YAML: automatic registered pipeline config at each source revision; common engine overrides `max_running_requests=64`, `cuda_graph_max_bs=64`. Client concurrency 1/16/32/64, seed order A42/B42/B43/A43, 16-request warmup, client token cap 2048 and unchanged native generation limit. Both ASR passes and all-request CAM++ similarity are verified. Mean metrics use arithmetic matched-seed means; percentiles below are seed ranges, never averaged. EN reports word WER, ZH character CER. First packet is N/A for completed responses.

### Non-streaming

| Concurrency | EN/ZH geometric throughput change |
| --- | ---: |
| 1 | +124.62% |
| 16 | +111.39% |
| 32 | +114.32% |
| 64 | +115.08% |

Each aggregate is `100 × (sqrt((PR_EN/main_EN) × (PR_ZH/main_ZH)) − 1)`, using per-language matched-seed mean req/s. These are integrated-bundle gains.

| Split / concurrency | req/s main → bundle | Mean / p95 latency (s), main → bundle | First packet | WER / CER (%) | CAM++ cosine | Failed / attempted |
| --- | --- | --- | --- | --- | --- | --- |
| EN / 1 | 0.8030 → 1.7840 (+122.17%) | 1.2445 / 1.762–1.773 → 0.5605 / 0.787–0.793 | N/A | 1.5281 → 1.5281 | 0.8243 → 0.8243 | 0 / 2176 → 0 / 2176 |
| EN / 16 | 5.7415 → 12.4915 (+117.57%) | 2.7725 / 3.757–3.972 → 1.2745 / 1.871–1.880 | N/A | 2.1393 → 1.1597 | 0.8135 → 0.8241 | 0 / 2176 → 0 / 2176 |
| EN / 32 | 7.9505 → 17.2925 (+117.50%) | 3.9865 / 5.681–5.682 → 1.8320 / 2.707–2.797 | N/A | 1.9635 → 1.1346 | 0.8153 → 0.8242 | 0 / 2176 → 0 / 2176 |
| EN / 64 | 10.4105 → 22.7895 (+118.91%) | 6.0340 / 8.378–8.693 → 2.7615 / 4.517–4.703 | N/A | 2.6920 → 1.1597 | 0.8119 → 0.8240 | 0 / 2176 → 0 / 2176 |
| ZH / 1 | 0.5370 → 1.2195 (+127.09%) | 1.8615 / 2.426–2.435 → 0.8200 / 1.063–1.071 | N/A | 2.1057 → 2.1010 | 0.8399 → 0.8399 | 0 / 4040 → 0 / 4040 |
| ZH / 16 | 4.6695 → 9.5905 (+105.39%) | 3.4195 / 4.521–4.577 → 1.6645 / 2.198–2.208 | N/A | 2.5529 → 1.9874 | 0.8370 → 0.8393 | 0 / 4040 → 0 / 4040 |
| ZH / 32 | 6.4620 → 13.6465 (+111.18%) | 4.9305 / 6.586–6.660 → 2.3340 / 3.100–3.117 | N/A | 4.0683 → 2.1495 | 0.8278 → 0.8395 | 0 / 4040 → 0 / 4040 |
| ZH / 64 | 8.6445 → 18.2680 (+111.33%) | 7.3510 / 9.572–9.849 → 3.4750 / 4.704–4.757 | N/A | 4.0150 → 2.0797 | 0.8279 → 0.8397 | 0 / 4040 → 0 / 4040 |

All recorded latency and RTF tail metrics improve in both seeds in all eight cells. At c1, matched-seed mean output duration and SIM are unchanged for both languages; EN WER is unchanged, while ZH differs by one and three recognition errors. At c16/32/64, shorter generated audio contributes to request-throughput gains: retain audio throughput and duration alongside req/s in the linked evidence. ZH16 seed43 SIM decreases 0.842155 → 0.841444 (−0.000711), despite the two-seed mean increasing.

The EN c1 seed43 20-second output with 90 insertion errors remains in both arms; its baseline/candidate WAV hashes match. One ZH1/A42 infrastructure attempt stopped at 1026/2020 when external CPU load exceeded the unchanged 2-core guard; it was archived, and a complete 2020-request replacement passed the same settings and verifier. No partial requests were spliced into the qualified result.

### Streaming

| Concurrency | EN/ZH geometric throughput change |
| --- | ---: |
| 1 | N/A |
| 16 | N/A |
| 32 | N/A |
| 64 | N/A |

Explicitly excluded by the Tiny non-streaming task scope; no streaming claim.

## Costs

Arithmetic mean startup, maximum sampled TTS-only memory across seeds, and graph counts (identical across seeds). ASR memory is excluded. Startup includes KDA compilation before readiness.

| Workload | Startup (s), main → bundle (delta) | Peak TTS memory (GiB), main → bundle (delta) | Graphs main → bundle (delta) |
| --- | --- | --- | --- |
| EN1 | 111.133 → 260.738 (+149.605) | 108.483 → 111.382 (+2.898) | 19 → 284 (+265) |
| EN16 | 120.113 → 278.255 (+158.141) | 109.263 → 111.499 (+2.236) | 19 → 284 (+265) |
| EN32 | 108.104 → 255.252 (+147.148) | 109.272 → 111.501 (+2.229) | 19 → 284 (+265) |
| EN64 | 107.605 → 255.760 (+148.155) | 109.300 → 111.616 (+2.316) | 19 → 284 (+265) |
| ZH1 | 108.117 → 256.773 (+148.656) | 109.632 → 109.147 (-0.484) | 19 → 284 (+265) |
| ZH16 | 108.610 → 255.734 (+147.124) | 108.542 → 111.495 (+2.953) | 19 → 284 (+265) |
| ZH32 | 111.618 → 267.746 (+156.128) | 109.276 → 111.515 (+2.238) | 19 → 284 (+265) |
| ZH64 | 109.119 → 263.720 (+154.601) | 109.310 → 109.386 (+0.076) | 19 → 284 (+265) |

The startup increase is approximately 147–158 seconds; sampled peak-memory changes vary by workload and are not an allocation guarantee.

## Tests

- Current-main integration `ea0958cb4199f7752427c6974e3c3527d96d80f3`: H200 **411 passed, 6 skipped**, covering Ming3/Ming-TTS, MPS, CPU locality, shared scheduler and stage environment; full pre-commit passed. Current-head [Omni CI](https://github.com/sgl-project/sglang-omni/actions/runs/40443535095) is pending; lint, docs and CodeQL passed. Manual unit-only preflight verified exact head `ea0958cb`, with all model stages disabled. The automatic PR workflow still stops at the documented draft gate.
- Full `pre-commit run --all-files` passed on measured head `6b87140`; the Tiny increment has identical file blobs on review head `99c78ed`.
- H200 arithmetic, Ming3-TTS, Ming-TTS, CUDA IPC, MPS and CPU-policy suites: **262 passed, 6 skipped**, exit 0. The skips are unsupported four-row strided normalization tiles; eager fallback remains available. Graph/eager equality and ownership/RNG regressions are included.
- CPU-only Tiny runner/vocoder imports passed with CUDA unavailable.
- Full clean-main matrix: **32/32 arms, 49,728 qualified requests**, zero failed/skipped, source/resources/contention and raw-evidence hashes independently verified off-node. The one invalid CPU-contention attempt is retained separately.
- A separate full EN64/seed42 smoke passed. Costly KDA intra/inter variants were prewarmed, but one shared KDA state variant still compiled during formal requests; this does not eliminate compilation from the entire KDA call graph.
- The Radix GPU assignment was released after confirming no remaining containers or GPU processes and verifying all 32 saved raw-result receipts.
- CI at head `99c78ed`: lint, docs, Rust, test layout, playback and NPU preprocessing passed; both NPU 950 and A3 ARM64 image builds passed. [Omni CI run 40332718657](https://github.com/sgl-project/sglang-omni/actions/runs/40332718657) stops at the documented draft gate; its skipped GPU jobs are not passes. Latest guide/resolver/workflows and live labels were checked: intended stage is `run-unit-test-ci-only`, with no Ming3 TTS end-to-end preset available. No stage label has been added while draft. Final current-main integration and dependency resolution remain pending; this PR is not merge-ready.
- Independent manual head validation: [Omni CI run 40333279462](https://github.com/sgl-project/sglang-omni/actions/runs/40333279462), exact head `99c78ed`. Preflight verified `run_unit_test=true`, all model stages false, no model preset; H100 environment setup passed. The accelerator suite passed: **1006 passed, 28 skipped, 9712 deselected** (524.40 s); target Tiny graph/vocoder/KDA/RNG tests executed, with 6 unsupported strided-normalization cases skipped. CPU partition A passed: **4270 passed, 61 skipped, 6415 deselected** (618.22 s); partition B passed: **5200 passed, 38 skipped, 5508 deselected** (801.18 s). The manual workflow and ephemeral-environment cleanup completed successfully. This documented workflow-dispatch validation does not clear the draft PR gate or validate final-main integration.
- Previous review repair at `8cbf592f`: H200 regression suites passed **236 tests**, with **6 unsupported strided-normalization cases skipped**; full local pre-commit passed. CodeQL no-effect protocol stubs now raise `NotImplementedError`. Previous-head [manual unit CI](https://github.com/sgl-project/sglang-omni/actions/runs/40439368237) targeted `8071abb0` and is superseded by this integration. The earlier queued run was cancelled by the final cookbook-only push; it is not counted as a pass. The automatic workflow remains blocked by the documented draft gate. The only documentation change is the explicitly requested `docs/cookbook/ming3_tts.md` update; no other `doc/` or `docs/` path is included.

Developed using [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) in [OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index); [complete paired evidence and historical experiments](https://github.com/Zhuofeng-Li/sglang-omni/blob/codex/ming3-tiny-c24-evidence/evidence/ming3-tiny-c24/report.md).
