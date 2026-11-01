# Ming3 final review: complete scoped default-off and mode pairs

Updated 2026-11-01T00:18:00.731459+00:00. **All16 scoped full-corpus arms completed and were strictly verified: 24864 formal requests, 0 failed.** Required review approvals, unresolved requests and final merged-main overall validation remain pending. No quality noninferiority margin was predeclared; zero failures do not establish quality acceptance or merge readiness.

## Measured sources and publication identity

Frozen pre-series main `74003d00f53e7f1a05593b556f21a31760a6fab6`. The experiment source was fixed throughout, including resumes; later publication changes deleted only the redundant12-case MPS-default test file. [Byte-level source proof](review-minimal-tests-source-proof.json), [source manifest](source-manifest.json), [plan](measurement-plan.json).

| PR | Measured source | Publication head |
| --- | --- | --- |
| #3136 | `78d8c310a65c14dd4bceb87e220c8304917805bb` | `97614b3aa844770b34c3d8c8ff360fd4e972b2bd` |
| #3189 | `35bf42ec695da774d6e1cf8731c70b291d671af9` | `75500328388a30af3a0a91e1190b36b178bf08f5` |
| #3190 | `2a636231d688b7bc83d78769e4f5162502680675` | `9dac9ab9715db96ee2bafbe1c974b7dc26d23e07` |

Full PR file lists remain16/15/2 files, with no doc/docs changes. Runtime, models, evaluator and configurations match the measured sources; the earlier416-case run includes the removed12 duplicates and is not relabeled as a fresh current-head run. Full all-files pre-commit passed on #3136 and the integrated publication source;24 resolved-config equivalence checks passed. Both Tiny and Dense inherit shared MPS off; explicit auto/on remain opt-ins. Main observed at this publication is `e727710aa6a0b29cef7dc362155c350dae313f21`. Current units incorporate main e727710a; if main advances again their source scope remains the recorded checkout. Native stack order is3136→3189→3190; draft3217 is excluded. Intermediate dense streaming stays accepted through full-response fallback until3190 enables incremental output.

## Protocol, coverage and raw evidence

One dedicated H200, same pinned image/assets/scorers, full SeedTTS EN1088 at concurrency16 and ZH2020 at concurrency1, seeds42/43 in A42/B42/B43/A43 order for each comparison. Default-off main→3136 was measured first, then final-source nonstream→stream. Per-arm cold caches, launch YAML, resolved config, native request reports, full WER/SIM IDs and audio hashes, capture events and sampled memory are retained. Reused main740 ZH A42 was predeclared before its results completed; its original comparison-context identifier is preserved, not rewritten. [Reuse provenance](reused-controls.json).

[Compact raw archive](completed-results.tar.gz), SHA256 **`14fba1d2ed1b2f07c2159c66fb6ae1744459ae7755f22b27f56c823498b13062`**; [strict16-arm verification](completed-arm-verification.json), [paired summary](paired-block-summary.json), [original mode-table readbacks](final-mode-blocks-body-receipts.json), [qualification-overview readbacks](qualification-intro-body-receipts.json), [original Tests readbacks](complete-ci-consolidated-body-receipts.json). These links refer to the complete16-arm snapshot. EN c16 and ZH c1 cannot be combined into a matched cross-language geometric number.

## Complete paired performance and quality

Means below are arithmetic means across the two matching seeds; p95 values are seed ranges. Main→3136 includes the sampling-storage lifetime correctness fix, so raw-main quality and length differences do not isolate pure optimization. Same-final-source mode pairs include that fix on both sides.

| Comparison / cell | req/s A→B | Response mean / p95 range ms A→B | First packet mean / p95 ms B | WER % A→B | CAM++ SIM A→B | Failed A→B |
| --- | --- | --- | --- | --- | --- | --- |
| Frozen main→3136 / ZH c1 | 0.9690→3.4565 (+256.71%) | 1032.0 / 1292.0–1330.0→289.0 / 377.0–381.0 | N/A | 0.644726→0.657739 | 0.779919→0.780319 | 0/4040→0/4040 |
| Frozen main→3136 / EN c16 | 9.0170→35.8540 (+297.63%) | 1765.5 / 2582.0–2642.0→443.5 / 606.0–636.0 | N/A | 1.088504→1.008959 | 0.778928→0.776780 | 0/2176→0/2176 |
| Final nonstream→stream / EN c16 | 35.6755→15.0010 (-57.95%) | 445.5 / 613.0–631.0→1061.5 / 1333.0–1337.0 | 659.1 / 759.0–772.4 | 0.996400→0.988026 | 0.776854→0.780522 | 0/2176→0/2176 |
| Final nonstream→stream / ZH c1 | 3.4510→2.1745 (-36.99%) | 289.5 / 377.0–378.0→460.0 / 594.0–594.0 | 155.5 / 191.3–193.6 | 0.661288→0.657739 | 0.780319→0.780663 | 0/4040→0/4040 |

**Frozen main→3136 / ZH c1:** WER +0.013013 percentage points (seed42 265→270 edits/42266 units; seed43 280→286 edits/42266 units); SIM +0.000400. Audio 5.201901→5.202059s (+0.003045%); output tokens seed42/43 131679/131017→131772/130932.

**Frozen main→3136 / EN c16:** WER -0.079545 percentage points (seed42 136→116 edits/11943 units; seed43 124→125 edits/11943 units); SIM -0.002148. Audio 3.948199→3.902500s (-1.157453%); output tokens seed42/43 54086/53305→53407/52741.

**Final nonstream→stream / EN c16:** WER -0.008373 percentage points (seed42 120→113 edits/11943 units; seed43 118→123 edits/11943 units); SIM +0.003669. Audio 3.904485→3.903309s (-0.030131%); output tokens seed42/43 53465/52737→53419/52751.

**Final nonstream→stream / ZH c1:** WER -0.003549 percentage points (seed42 274→268 edits/42266 units; seed43 285→288 edits/42266 units); SIM +0.000344. Audio 5.202059→5.202059s (+0.000000%); output tokens seed42/43 131772/130932→131772/130932.

**Adverse results remain explicit:** default-off ZH WER rises in both seeds; default-off EN SIM and audio duration decrease. Final EN c16 streaming throughput falls57.95%, and its mean first packet is slower than the nonstream complete response; EN seed43 has more WER edits even when the two-seed mean improves; ZH seed43 likewise worsens285→288 edits. The ZH row above reports its own matched tradeoff without extrapolating across concurrency. All final streaming requests have valid positive first packets. All PR/default-off and final-mode formal requests report stop and zero reported length finishes; raw main has6216 unknown finish reasons, which cannot prove absence of truncation. No predeclared margin means none of these mean deltas is promoted to a quality acceptance decision.

## Startup, memory and graph costs

| Comparison / cell | Startup mean s A→B (delta) | Maximum observed device GiB A→B (delta) | Successful capture events/arm A→B |
| --- | --- | --- | --- |
| Frozen main→3136 / ZH c1 | 93.605→143.174 (+49.569) | 107.4209→109.1416 (+1.7207) | 19→430 |
| Frozen main→3136 / EN c16 | 96.096→130.143 (+34.048) | 108.6943→109.6221 (+0.9277) | 19→430 |
| Final nonstream→stream / EN c16 | 137.170→140.674 (+3.504) | 108.8389→110.0674 (+1.2285) | 430→430 |
| Final nonstream→stream / ZH c1 | 152.698→136.177 (-16.521) | 108.3447→108.7490 (+0.4043) | 430→430 |

Memory is a sampled maximum at nominal1s cadence, with actual gaps in the raw logs; it is not a guaranteed instantaneous peak. Successful capture_end events are not necessarily unique resident graphs. [Vocoder setup component audit](graph-setup-review-resolution-audit.json) preserves384 graphs, shared input/output backing5,505,024bytes=5.25MiB, and default-off setup EN34.270s / ZH43.711s seed means. Setup phases overlap other stage initialization, so these are not additive attribution of the total startup delta. Explicit shared buffers exclude graph-pool/model memory.

## Complete current-head selected Omni CI

All three selected Omni CI runs completed successfully on the publication heads, with the #3136 accelerator retry caveat below. [Per-job attempt/count/source/hash verification](test-cleanup-current-unit-verification.json), complete proofs for [#3136](pr3136-test-cleanup-complete-ci-verification.json), [#3189](pr3189-test-cleanup-complete-ci-verification.json), [#3190](pr3190-test-cleanup-complete-ci-verification.json), and [original Tests consolidation/readback](complete-ci-consolidated-body-receipts.json). Earlier-head CI chronology remains in the immutable prior report linked below. Current unit checkouts are #3136 `2e3fb3e6`, #3189 `bebb1769`, #3190 `ba485f4b`, matching the prospective integrations with main e727710a. Passed/skipped counts:

| PR | CPU A | CPU B | CPU C | Accelerator | Selected model stage |
| --- | --- | --- | --- | --- | --- |
| #3136 | 3307 / 45 | 3806 / 26 | 3532 / 55 | 1213 / 31 (attempt2) | Passed, Higgs DP2 |
| #3189 | 3267 / 36 | 3813 / 28 | 3605 / 62 | 1214 / 31 | Not selected |
| #3190 | 3267 / 36 | 3814 / 28 | 3605 / 62 | 1214 / 31 | Not selected |

**#3136 accelerator retry retained:** [causal/source audit](pr3136-test-cleanup-accelerator-retry-audit.json). Attempt1 had1 failure/937 passed/29 skipped in Qwen3-TTS final-code CUDA IPC (child zeros instead of sevens); automatic attempt2 passed1213/31. The direct-call test, adapter/default-stream handoff, serializer and payload code are byte-identical to main e727710a, but root cause and preceding-test interactions remain unproven. The two reference main-development CI runs passed the test, so they do not establish a baseline failure. No manual rerun, assertion weakening or clean-first-pass claim. #3189/#3190 units passed on their first attempts. All parsed attempts, including the failure, remain in the job verification.

**Selected Higgs MPS artifact:** ID13060975886, ZIP SHA256 `d1effdeefd3d7a4574189c8475cba84a3918f92cfa2c7fd8d9e0ffdce185da4e`. Actual exact-head checkout97614b3a, DP2 independent weights;1088 unique canonical successful requests and8 successful canaries. Independent artifact checks verified matching request/scorer IDs, WER arithmetic, UTMOS/SIM means, calibrated performance/configured quality validation, model-path overlap above uncertainty, and all6 process/port/GPU/MPS cleanup conditions with empty post-cleanup clients/ports/PIDs. WER/UTMOS cover1088, preset SIM covers50. Canonical finish reasons are unknown; no truncation-free claim. This exact-head Higgs model-stage coverage is separate from the newer-main synthetic unit trees and from Ming paired quality.

ASR/TTS/Omni stages were unselected; companions also did not select MPS. Workflow_dispatch-only ephemeral-home cleanup was skipped, not passed. Skips/deselections are not hardware/model/cleanup passes. All16 scoped corpus arms are now complete; other head checks, approving reviews and final merged-main overall validation remain separate gates; selected Omni CI success is not merge readiness.

The [old factory import-path P1](legacy-vocoder-review-resolution-audit.json) was individually audited/resolved with retained identical regression and416-case coverage. The [cookbook clarification](cookbook-current-revision-clarification-receipt.json) corrects the historical auto/docs reply; that request remains open and no docs edit or approval is claimed.


## Additional individually verified review resolutions

The following requests were resolved only after checking the fresh publication head, actual CI source blobs/named passes and author resolution permission. These are targeted request resolutions, not review approvals or a blanket resolution of outdated threads.

| Original request | Verified handling | Audit |
| --- | --- | --- |
| #3136 explicit-stage compatibility4383657372 | New factory keywords have backward-compatible defaults; actual current unit-A passed the old-signature case and both omitted-device preprocessing cases | [Source/default/current-CI audit](explicit-stage-review-resolution-audit.json) |
| #3189 CPU vocoder fallback4396752939 | Complete terminal latents retained for CPU paths;26 current routing/model/device/request combinations plus direct CPU decode passed. GPU engine infrastructure is stubbed in the CPU regression; XPU selection is mocked, not hardware qualification | [Named cases and exact blobs](cpu-vocoder-review-resolution-audit.json) |
| #3189 nonstream finish reason4381483173 | Nonstream copies finish reason through audio payload rebuild; current CPU stop and CUDA-graph length assertions passed | [Source and current CI](finish-reason-review-resolution-audit.json) |
| #3136 inherited MPS off4432962390 | Model-specific field/override removed; current Tiny/Dense off/round-trip cases passed; all3 original bodies separately identify default-off and historical optional-auto measurements | [Config/source/CI/body audit](mps-default-review-resolution-audit.json) |

The cookbook request, latency/throughput tradeoff discussion, required approvals and coordinated #3189/#3190 landing remain separate open gates. Historical Tiny c1/c32 TTFA/underrun data is retained at its actual older source in the linked earlier streaming evidence, including real c32 underruns and its128-sample/warm-cache scope; it is not relabeled as current-head or full-corpus qualification. No new Tiny experiment was started merely because that evidence is older. Remaining final-head ZH mode arms continue on the dedicated H200; no source/test changes or experiment restart accompanied these resolutions.


## Additional source and current-CI review audits

The following resolved code-review requests have source identity and named current-CI case evidence; resolving a thread does not supply reviewer approval or complete performance qualification.

- [Already-main Qwen guard removal](already-main-guard-review-resolution-audit.json): the unrelated file is absent from the PR diff and byte-identical to the actual main comparison.
- [Tiny defaults and operator overrides](tiny-defaults-overrides-review-resolution-audit.json): retained Tiny execution defaults, dense-only GPU preprocessing placement and explicit graph/mixed/chunk overrides.
- [Full-width PCI domain](pci-domain-review-resolution-audit.json): six mocked NVML/sysfs cases cover normal/large domains and fallback without mutating affinity; no large-domain hardware claim.

The original #3189 body now explicitly retains the historical Tiny c32 playback underruns from measured integration `251f02b467fe06269cb2d3d8c1063565d7c3de82`, Tiny runtime `5c955911`: mean maximum EN229.5ms and ZH129.7ms. These are warm-cache first128-sample latency observations, not new-head or full-corpus quality results. See [body readback receipt](pr3189-historical-tiny-limit-body-receipt.json) and the earlier streaming-review evidence. The earlier12-arm snapshot remains available through the [immutable prior report](https://github.com/Zhuofeng-Li/sglang-omni/blob/90e529eeb80eeaffaf21be35682cc9c0a10a01c1/evidence/ming3-final-review-20261031/v3/report.md); the current archive contains all16 completed arms.

### Exact solver and weight-update review verification

- [Exact solver audit](exact-solver-review-resolution-audit.json): two isolated exact-equality guidance/drift/noise cases and three zero-velocity solve temperatures passed in both attempts of the current accelerator CI job. This retains the unrelated first-attempt Qwen IPC failure and successful automatic full retry; no widening of the transformer tolerance or new GPU experiment.
- [Live reload audit](live-reload-review-resolution-audit.json): current unit-C verifies a second load is rejected before parameter mutation. Whole-pipeline restart remains required and explicit in the PR Changes. Online refresh of preprocessing replicas and captured constants is unsupported.

Both original code requests are now resolved after exact publication/actual-CI source blob checks and fresh thread permissions. Required reviewer approval and final merged-main overall validation remain pending.

### Shared streaming backend review verification

[Current shared-decoder audit](shared-decoder-review-resolution-audit.json) verifies publication/actual-CI blob identity for the shared modules, both model adapters, compatibility export and three test files. Six named current CPU CI cases passed for multi-request batching, fixed-slot isolation and cancellation/reset behavior. The original #3189 Changes records the extraction. The code reuse request is resolved; this does not close the performance/underrun discussion, imply new-head Tiny full-corpus quality, or waive paired landing of #3189/#3190.

### Bounded cache, fusion switch and graph setup review verification

- [Bounded-cache audit](cache-budget-review-resolution-audit.json): two64MiB cache budgets, zero-entry bypass and seven current CPU test passes cover seeded/fresh equality, seed changes, unseeded/URL bypass and byte-budget eviction. Dense-only120s default and pre-encode checks were source-audited; no new long-duration runtime test or unique-reference throughput claim.
- [Fusion switch and diagnostic audit](fused-switch-review-resolution-audit.json): explicit factory switch reaches the model, selected path is logged once and missing Triton import is logged. Current CUDA fused/module comparison and CPU checkpoint-default cases passed. The earlier ENc32 fusion ablation retains its original measurement revision and is not a new-head isolated gain.
- [Vocoder graph setup audit](graph-setup-review-resolution-audit.json): shared flat buffers, preserved strides and longest-first capture; current CPU/CUDA bit-for-bit cases pass. The four default-off #3136 arms log384graphs and5,505,024 explicit shared input/output bytes each. Setup wall time EN seed42/43=34.425/34.115s, mean34.270s; ZH=49.810/37.612s, mean43.711s. These phase wall times overlap other stage initialization and are not additive attribution of total startup. Explicit buffers exclude graph-pool/model/device peak. [All3 original Costs body readbacks](graph-setup-body-receipts.json) verified.

The graph audit was observed from the private15-arm snapshot, whose identity remains recorded. Its four completed-arm log member hashes also match the [immutable12-arm archive](https://github.com/Zhuofeng-Li/sglang-omni/blob/90e529eeb80eeaffaf21be35682cc9c0a10a01c1/evidence/ming3-final-review-20261031/v3/completed-results.tar.gz) (`a2aadf3cb4e84187b75410634cfd010d6c9976d40fc968b05c9a1c46bd61718d`), as independently checked in the audit. That historical observation retained the incomplete ZH status at that time; current16-arm completion is established by the verification above. The three code requests were resolved after fresh source/head/thread checks; reviewer approval remains required.

## Integration boundary and remaining gates

Observed actual main is `e727710aa6a0b29cef7dc362155c350dae313f21`. The final publication prefix has prospective tree `120a16195fd895d684d8599486da1ba939c1eb11` on e727710a and current unit checkout ba485f4b; that unit coverage does not establish merged-main performance/quality equivalence. Main #3030 changes shared startup/normal-loop/pending-batch handling even with speculative overlap disabled. Actual merged-main source audit/smoke and overall paired validation against frozen main740 remain mandatory after landing. Conditional reuse is only eligible if its declared source/protocol/hardware conditions are proven; no extra run or merged status is claimed here.

Required reviews and unresolved requests are independent of selected CI and these pairs. The cookbook request remains open: current source PRs contain no doc/docs edits, and the earlier auto/docs reply was explicitly corrected. #3189 performance/underrun discussion and coordinated prefix landing remain separate. Merge only the validated3136→3189→3190 prefix, never draft3217, and do not bypass repository protections.

## Historical evidence and interpretation limits

The [immutable prior report](https://github.com/Zhuofeng-Li/sglang-omni/blob/90e529eeb80eeaffaf21be35682cc9c0a10a01c1/evidence/ming3-final-review-20261031/v3/report.md) retains all earlier current-main matrices, corrected-lifetime control, optional MPS/cache/fusion ablations, repeated scoring, old CI chronology and their exact sources, with one evidence index. The earlier optional MPS-enabled ENc16 comparison remains main740 off→b6d7auto,8.863→41.617req/s; it is not the default-off result or isolated MPS gain. Historical Tiny timing remains measured integration251f02b4/Tiny runtime5c955911, first128 EN/ZH samples,2seeds, warm service/caches, c1/c32 and server limit32. Tiny c32 had real mean-maximum playback underruns EN229.5ms and ZH129.7ms, with single-packet requests N/A. It is not current-head/full-corpus Tiny quality qualification.

Native throughput lacks absolute per-request start/end timestamps for independent recomputation. Raw reports, matching request/scorer IDs, WER arithmetic, per-request SIM and audio hashes were checked; these checks do not constitute an independent experiment rerun. Minimal results/score/hash/cost evidence is backed up privately and published here; WAVs, weights and caches are excluded. No assignment credentials or authentication state are published. The separate8B200 Muse allocation was not modified.

Developed through [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) in [OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index), with co-author [Ethan Feng](https://yichenfeng.me/).

## Original quality-review response

The [original #3190 corpus-quality review has been answered](https://github.com/sgl-project/sglang-omni/pull/3190#issuecomment-6551076083) after all3 original bodies and the complete16-arm evidence were published and read back. [Reply receipt](final-quality-review-reply-receipt.json), [complete evidence publication identity](complete16-evidence-publication.json), [fresh head/check/review state](complete16-current-pr-state.json). At this observation no head checks failed or remained incomplete, while #3136 still had CHANGES_REQUESTED and both companions REVIEW_REQUIRED. No merge or reviewer approval is claimed.
