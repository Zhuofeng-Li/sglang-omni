# Ming3 final review: inherited default MPS off

Updated 2026-10-31T21:57:22.059933+00:00. Qualification is incomplete; no merge-readiness claim.

## Source and review fixes

Frozen main `74003d00f53e7f1a05593b556f21a31760a6fab6`; #3136 `78d8c310a65c14dd4bceb87e220c8304917805bb`, #3189 `35bf42ec695da774d6e1cf8731c70b291d671af9`, #3190 `2a636231d688b7bc83d78769e4f5162502680675`. Main #3355 is integrated. Later `3cb3c6cc` changes Ming-ASR only and was audited separately from Ming3-TTS and the Qwen3-ASR scorer. Draft #3217 is excluded. Full individual diffs have 17/15/2 files and no doc/docs changes.

[Maintainer review](https://github.com/sgl-project/sglang-omni/pull/3136#discussion_r4432962390) requests shared default `mps: off` for Tiny and dense. The model override and redundant field are removed. Explicit off/on/auto remain supported. Companion commits carry only this dependency fix; #3189 still accepts dense streaming requests through complete-response fallback until #3190 enables incremental output. Existing CPU vocoder full-response fallback remains covered.

Full all-files pre-commit passed. Pinned-runtime GPU/host regressions: **416 passed, zero skipped**. New cases cover inherited defaults, explicit modes, round trips and explicit stages. Resolved config equivalence separately compares every field for Tiny/dense and all four mode selections against the corresponding prior branch; explicit configurations must remain unchanged. Controller integrated config collection lacked Torch and is not counted as passed.

## Subsequent review cleanup: test-only publication heads

[Maintainer feedback](https://github.com/sgl-project/sglang-omni/pull/3136#discussion_r4433447951) requested removal of the redundant MPS-default test file. Publication heads are now #3136 `97614b3aa844770b34c3d8c8ff360fd4e972b2bd`, #3189 `75500328388a30af3a0a91e1190b36b178bf08f5`, #3190 `9dac9ab9715db96ee2bafbe1c974b7dc26d23e07`. For each branch, [source proof](review-minimal-tests-source-proof.json) shows the sole tree delta from its recorded measured head is deletion of `tests/unit_test/ming3_tts/test_mps_defaults.py` (51 lines, 12 parametrized cases). Runtime/model/evaluator/config files are unchanged. The existing Tiny/Dense checkpoint-default and config round-trip test remains. Recorded 416-case results include the now-removed cases and are not relabeled as a fresh run. Full all-files pre-commit passed on #3136 and the final integrated branch. New-head CI is running or queued and must be verified independently. All three original PR bodies and heads were [read back](review-minimal-tests-publication.json); individual own patches are now16/15/2 files, doc/docs-free. The original thread was replied to; no claim of reviewer approval. The frozen-source experiment queue continues without restart.

## Protocol and valid reuse

See [plan](measurement-plan.json), [source identities/archive hashes](source-manifest.json), [reuse provenance](reused-controls.json). One dedicated H200, identical pinned image, model/data assets, observer and scorers are reused; no weights or environment reinstall. Full EN1088 c16 and ZH2020 c1; two seeds42/43 ABBA. First qualify default-off main → #3136 (ZH first, then fresh EN); then final #3190 non-streaming → streaming quality/failures, also ABBA for both languages. Each arm saves YAML, resolved defaults, private cold caches, native speed/quality reports, per-request SIM/IDs/audio hashes, capture logs and sampled memory.

The previously running main740 ZH A42 control already uses native MPS off, with unchanged source/image/GPU/assets/settings. Reuse was elected before its result finished. Preserve its original raw config, including old `candidate_commit` as comparison context; actual measured source is main740. Do not rewrite it as a new candidate measurement. Old queue is held while that control finishes quality, then terminated without starting an old-auto candidate. New GPU tests and candidate measurements start only after its container exits. Raw coverage/scoring/costs must be verified before accepting reuse.

## Complete default-off paired blocks; final-mode corpus checks pending

Both full-corpus two-seed ABBA blocks are complete: frozen main74003d00 → measured #3136 head78d8c310, inherited MPS off on both sides. Publication-head test-only equivalence is documented above. [Strict verification](completed-arm-verification.json), [paired summary](paired-block-summary.json), [original-body readbacks](default-off-blocks-body-receipts.json), [compact raw evidence](completed-results.tar.gz). The original eight-arm publication snapshot has SHA256 `dbddf598e87c38c52e3319b420afb0970408d3c87e05ee2b758d93bcd1871904` ([immutable archive](https://github.com/Zhuofeng-Li/sglang-omni/blob/c867876c/evidence/ming3-final-review-20261031/v3/completed-results.tar.gz)); its publication receipts retain that hash. The current raw archive and strict verification now include twelve complete arms, with the same unchanged default-off native results. Native seed means are arithmetic; p95 is a seed range.

| Condition | req/s main → PR | Latency mean / p95 range s, main → PR | WER % main → PR | CAM++ SIM main → PR | Failures |
| --- | --- | --- | --- | --- | --- |
| ZH c1 | 0.9690 → 3.4565 (+256.71%) | 1.0320 / 1.292–1.330 → 0.2890 / 0.377–0.381 | 0.644726 → 0.657739 (+0.013013 pp) | 0.779919 → 0.780319 (+0.000400) | 0/4040 → 0/4040 |
| EN c16 | 9.0170 → 35.8540 (+297.63%) | 1.7655 / 2.582–2.642 → 0.4435 / 0.606–0.636 | 1.088504 → 1.008959 (-0.079545 pp) | 0.778928 → 0.776780 (-0.002148) | 0/2176 → 0/2176 |

| Condition | Startup s main → PR (delta) | Observed peak GiB main → PR (delta) | Capture events each arm |
| --- | --- | --- | --- |
| ZH c1 | 93.6055 → 143.1740 (+49.5685) | 107.4209 → 109.1416 (+1.7207) | 19 → 430 (+411) |
| EN c16 | 96.0960 → 130.1435 (+34.0475) | 108.6943 → 109.6221 (+0.9277) | 19 → 430 (+411) |

ZH c1: seed42 265→270 edits; seed43 280→286 edits. Audio duration mean 5.201901→5.202059s (+0.003045%); output tokens seed42/43 131679/131017→131772/130932.

EN c16: seed42 136→116 edits; seed43 124→125 edits. Audio duration mean 3.948199→3.902500s (-1.157453%); output tokens seed42/43 54086/53305→53407/52741.

**Adverse results retained:** ZH WER rises in both seeds; EN SIM falls in aggregate, audio is about1.16% shorter, and EN seed43 WER has one additional edit despite the better two-seed mean. No quality noninferiority margin was predeclared. Raw main contains the known sampling-storage lifetime bug, so these results mix its correctness fix with optimization effects and do not isolate pure optimization gains. Main exposes no stop reasons (EN2176, ZH4040 unknown); PR reports stop for all formal requests, zero reported length finishes. Unknown main reasons do not prove absence of truncation. EN c16 and ZH c1 are different conditions and cannot form a matched EN/ZH geometric gain. Capture counts are successful events, not necessarily unique resident graphs. Memory is observed, not guaranteed true peak.

The final-head EN mode block is complete and reported below; the remaining ZH mode checks run on the original fixed source and protocol. The full campaign is incomplete, and no final-series quality or merge-readiness claim is made. The earlier auth boundary and partial snapshots remain available in immutable evidence history; no completed measurement was restarted.

## Complete final-head EN c16 mode comparison; ZH pending

Full EN1088, seeds42/43, A42/B42/B43/A43 on the same measured final source `2a636231d688b7bc83d78769e4f5162502680675` and dedicated H200; A=nonstreaming, B=streaming, inherited MPS off. Both sides include the sampling-storage lifetime correction. Publication head9dac9ab9 has only the separately documented test-file deletion. Original mode tables and costs were [updated/read back on all three PRs](final-mode-blocks-body-receipts.json). [Raw compact evidence](completed-results.tar.gz), [strict verification](completed-arm-verification.json), [paired summary](paired-block-summary.json): now12 acknowledged complete arms, snapshot SHA256 `a2aadf3cb4e84187b75410634cfd010d6c9976d40fc968b05c9a1c46bd61718d`. These are mode differences on one source, separate from main→PR gains. ZH mode block remains incomplete.

| EN c16 metric | Nonstreaming | Streaming | Difference / interpretation |
| --- | ---: | ---: | --- |
| req/s, seed mean | 35.6755 | 15.0010 | **-57.95% throughput** |
| Response mean ms | 445.5 | 1061.5 | Higher for streaming |
| Response p95 ms, seed range | 613–631 | 1333–1337 | Higher for streaming |
| First audio packet mean ms | N/A | 659.1 | Exceeds nonstreaming complete-response mean445.5ms |
| First audio packet p95 ms, seed range | N/A | 759.0–772.4 | All2176 stream requests have valid positive packets |
| WER % | 0.996400 | 0.988026 | -0.008373 pp |
| CAM++ SIM | 0.776854 | 0.780522 | +0.003669 |
| Failures | 0/2176 | 0/2176 | Both modes report stop for all; zero reported length finishes |
| Audio duration mean s | 3.904485 | 3.903309 | -0.030131% |
| Startup mean s | 137.1705 | 140.6740 | +3.5035s |
| Maximum observed device GiB across seeds | 108.8389 | 110.0674 | +1.2285GiB |
| Successful capture events each arm | 430 | 430 | +0 events; unique resident graph count not established |

WER changes in opposite directions by seed: seed42 120→113 edits, seed43 118→123, each over11943 reference words. Output-token totals seed42/43 are53465/52737→53419/52751. The improved mean WER/SIM does not erase the throughput/latency cost or establish noninferiority; no acceptance margin was predeclared. Nominal1s memory polls retain actual gaps; observed maximum is not a guaranteed instantaneous peak. The remaining four full ZH c1 mode arms continue under the fixed protocol, without restarts or source changes.

## Historical optional MPS on

The [prior source record](../v2/report.md) retains the completed EN c16 ABBA on main740off → PR3136b6d7auto: mean req/s8.863→41.617 (+369.56%), WER1.075944%→0.996400%, CAM++SIM0.778832→0.776681, zero failures/2176 per side, audio3.945993→3.903199s. Startup94.1145→137.1715s; observed peak108.6943→109.6670GiB; successful capture events19→430. This is whole-candidate optional-MPS performance, not an isolated MPS benefit or default-off result. SIM regresses and output length differs. Main contains the sampling-storage lifetime correctness bug, so raw-main differences mix the fix with optimization effects.

The [complete earlier qualification and trajectories](../../ming-review-20261028/report.md) preserve earlier source identities, the full historical matrix, corrected-lifetime controls, repeated scoring, adverse deltas and ablations. They are not relabeled as current-head measurements. Both complete default-off blocks and the final-head EN mode block are reported above; the final-head ZH mode block remains pending. No quality margin was predeclared.

## New main integration checkpoint

Main subsequently advanced to `e727710aa6a0b29cef7dc362155c350dae313f21`: #3030 speculative decode overlap and #2854 PersonaPlex radix guard. The fixed corpus campaign continues on its recorded sources. Read-only prospective final-prefix integration is conflict-free, tree `ffa0d2776a5c821974ed17d8aa174a1f1a9823e2`; its own 29-path patch remains doc/docs-free. [Integration audit](main-e727-integration-audit.json) and [original-body readback receipts](main-e727-body-receipts.json) record this boundary. Existing selected CI is valid for its recorded checkout, but does not cover this new integration. Non-speculative Ming keeps overlap disabled; new shared startup and pending-batch handling still need final integration verification. Prior exact-tree reuse proof is historical, not sufficient for the new main. No extra performance conclusion or merge-readiness claim follows from a clean merge-tree.

## New-head CI setup and targeted review resolution

All three new-head gate/preflight and shared setup jobs passed. [Setup source identities](test-cleanup-setup-source-identities.json) verify synthetic checkouts: #3136 `2e3fb3e6dbd841b10f1dbfe38d3a1bb8c0c651c6`, #3189 `bebb17690054d4069e1cbfbbc91ab579770ba962`, #3190 `ba485f4b529e667bd92fcc9491d1f2adb6d7351f`. The final setup tree `120a16195fd895d684d8599486da1ba939c1eb11` matches the updated prospective merge and includes main e727710a. At that setup checkpoint, actual unit/model job checkouts and results were unverified; setup is not a test pass. Subsequent verified partitions are recorded below. [Original-body receipts](test-cleanup-setup-body-receipts.json) record this distinction. Existing labels are unchanged: PR Test plus selected Higgs MPS for #3136, PR Test only for the companions.

Only the specific duplicate-test request4433447951 was [resolved](minimal-tests-thread-resolution.json), after current-head deletion, unchanged existing regression, complete pre-commit and author resolution permission were verified. Other threads and required approvals remain independent. The default-off full-pair results were [replied to in the original MPS-default thread](complete-default-off-review-reply-receipt.json); no reviewer approval is inferred.

## Subsequent current-run unit results (selected CI incomplete)

[Per-job log/hash/source verification](test-cleanup-current-unit-verification.json) and [final-prefix accelerator verification](pr3190-test-cleanup-accelerator-verification.json) record eight successful terminal partitions at that checkpoint, including one accelerator job that required an automatic retry; the first failure is preserved below. Counts below are passed / skipped; skipped and deselected cases are not passes. Checkouts match the recorded setup identities and prospective integrations with main e727710a. Original Tests sections were updated and read back for [#3136](pr3136-test-cleanup-cpu-body-receipt.json), [#3189](pr3189-test-cleanup-cpu-body-receipt.json), [#3190](pr3190-test-cleanup-accelerator-body-receipt.json).

| PR | CPU A | CPU B | CPU C | Accelerator | MPS |
| --- | --- | --- | --- | --- | --- |
| #3136 | 3307 / 45 | 3806 / 26 | 3532 / 55 | 1213 / 31 on attempt2; attempt1 failed | Selected Higgs, queued |
| #3189 | 3267 / 36 | 3813 / 28 | 3605 / 62 | 1214 / 31 | Not selected |
| #3190 | Pending | Pending | Pending | 1214 / 31 | Not selected |

#3189 selected Omni CI subsequently completed successfully; all four unit partitions passed on their first attempts. [Complete current-run verification](pr3189-test-cleanup-complete-ci-verification.json), [original-body readback](pr3189-test-cleanup-complete-ci-body-receipt.json). PR Test only was selected; unselected stages and dispatch-only ephemeral-home cleanup skips are not model/hardware/cleanup passes.

**#3136 accelerator retry:** [causal/source audit](pr3136-test-cleanup-accelerator-retry-audit.json), [original-body readback](pr3136-test-cleanup-accelerator-retry-body-receipt.json). Attempt1 had1 failure/937 passed/29 skipped in Qwen3-TTS cross-process final-code CUDA IPC (zeros instead of sevens); the workflow automatically reran the suite and attempt2 had1213 passed/31 skipped. This is not a clean first pass. The failing direct-call test, adapter/default-stream handoff, serializer and payload code are byte-identical to main e727710a. Root cause and preceding-test interactions remain unproven. Two [reference main-development PR CI runs](main-reference-pr-accelerator-observations.json) passed that test on their recorded earlier checkouts; they do not establish a baseline occurrence of this failure. No manual rerun, weakened assertion, or extra GPU job was used. The artifact verifier now retains every parsed attempt and rejects unparsed retry failures.

The previously fixed old factory import-path P1 was separately [audited and resolved](legacy-vocoder-review-resolution-audit.json): all three branches retain the same factory export, the identical import/signature regression remains and was included in the416-case pinned-runtime run. This resolves only that request; it does not grant review approval or close the cookbook request.

A [current-revision clarification](cookbook-current-revision-clarification-receipt.json) in the original cookbook review distinguishes the historical auto/docs reply from the current inherited-off, code/test-only patch. That cookbook request remains open; no docs edit or reviewer approval is claimed. Corpus source identities stay frozen, and incomplete final-mode blocks still have no paired aggregate.

## Interpretation and storage limits

Means are matched-seed arithmetic means; p95 is a seed range. EN c16 and ZH c1 cannot form a cross-language geometric summary. Preserve failures and adverse WER/SIM changes. Finish-reason observability is separate from native token-cap counts; the raw-main non-stream WAV control did not expose stop reasons, whereas the new candidate does; retain the actual per-arm coverage. Native throughput reports lack absolute per-request timestamps for independent recomputation. Memory is observed maximum with actual raw poll gaps retained; successful capture events need not be unique resident graphs.

Minimal result/score/request/hash/cost evidence is continuously backed up to private controller scratch; WAVs, weights and runtime caches remain on the node and are excluded. Source SHA and runtime probes are verified. Public provenance excludes private assignment/authentication files. Earlier measured-head Omni CI runs are [#3136](https://github.com/sgl-project/sglang-omni/actions/runs/41235981255), [#3189](https://github.com/sgl-project/sglang-omni/actions/runs/41235989382), [#3190](https://github.com/sgl-project/sglang-omni/actions/runs/41236000842). All three gates/preflights passed. Existing labels select PR Test plus Higgs MPS for #3136 (`examples/mps_dp/configs/higgs_h100_dp3.yaml`), and PR Test only for #3189/#3190. Other model stages were not selected. PR Test runs after successful setup for any selected stage, even when the resolver-specific `run_unit_test` flag is false. Shared setup passed on all three current heads; PR Test partitions are running or queued, and model stages remain pending. #3190 accelerator subsequently passed **1214 cases / 31 skipped**. Actual checkout `a6549eaef6cc4a0d790ce7a4e1bf0e753e49e632`, tree `66b5237126b03481b98668135242b0c0c5c8d913`, differs from the measured head by exactly the previously audited main740 → main3cb3 Ming-ASR #2977 patch. The three added skips are optional Ming-ASR checkpoint batch cases; the previous 28 skip identities remain. This is a synthetic integration checkout, not an identical head tree. Its main-only cookbook update is not a PR docs change: freshly fetched PR file lists remain 17/15/2, all doc/docs-free. #3190 Omni CI subsequently completed **successfully**: unit-A **3307 passed / 37 skipped**, B **3723 / 57**, C **3651 / 32**, accelerator **1214 / 31**. All four unit jobs checked out that same synthetic integration commit/tree. Only PR Test was selected; ASR/TTS/MPS/Omni stages were skipped as unselected, and independent ephemeral-home cleanup was skipped because it is workflow_dispatch-only. These skips are not model/hardware or cleanup passes. #3189 Omni CI also completed **successfully**: unit-A **3306 passed / 37 skipped**, B **3723 / 57**, C **3651 / 32**, accelerator **1214 / 31**. Actual checkout `ca6f8cb7903a202088fe67e0f21edd85baa2b9cb`, tree `a794c682ec13f56527cdee4d73cdeecfe7bf23bf`, again differs from its head by exactly the audited main3cb3 patch. It selected PR Test only; unselected model stages and workflow_dispatch-only cleanup are skips, not passes. #3136 Omni CI also completed **successfully**: unit-A **3238 passed / 36 skipped**, B **3798 / 28**, C **3604 / 62**, accelerator **1213 / 31** at synthetic `c341888db34fde9c8259e68390882556db5f4a4c`, tree `8fe7611ae58dea5a0311f52d0c6c588d7c6acb07`, with exactly the audited main3cb3 patch. Its selected Higgs MPS job checked out the exact head78d8c310; artifact13057435796 passed correctness, overlap, calibrated performance/quality and all six process/port/GPU/MPS cleanup checks: 1088 canonical requests, zero failures, plus eight canary requests, DP2 independent weights. WER/UTMOS cover1088 and the configured similarity subset covers50; this is shared-path Higgs coverage, not Ming corpus quality. ASR/TTS/Omni were unselected; independent ephemeral-home cleanup remains workflow_dispatch-only and skipped. All three earlier measured-head selected Omni CI runs are verified complete; Ming corpus pairs and approving review remain pending. Exact head identities and parsed preflight are saved alongside this report. Original PR bodies and all three head identities were read back after publication; [maintainer-thread reply](https://github.com/sgl-project/sglang-omni/pull/3136#discussion_r4433076884). CI and human review must be verified separately before landing the qualified prefix.

Developed through [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) in [OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index), with co-author [Ethan Feng](https://yichenfeng.me/).
