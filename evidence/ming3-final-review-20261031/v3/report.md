# Ming3 final review: inherited default MPS off

Updated 2026-10-31T19:48:27.689990+00:00. Qualification is incomplete; no merge-readiness claim.

## Source and review fixes

Frozen main `74003d00f53e7f1a05593b556f21a31760a6fab6`; #3136 `78d8c310a65c14dd4bceb87e220c8304917805bb`, #3189 `35bf42ec695da774d6e1cf8731c70b291d671af9`, #3190 `2a636231d688b7bc83d78769e4f5162502680675`. Main #3355 is integrated. Later `3cb3c6cc` changes Ming-ASR only and was audited separately from Ming3-TTS and the Qwen3-ASR scorer. Draft #3217 is excluded. Full individual diffs have 17/15/2 files and no doc/docs changes.

[Maintainer review](https://github.com/sgl-project/sglang-omni/pull/3136#discussion_r4432962390) requests shared default `mps: off` for Tiny and dense. The model override and redundant field are removed. Explicit off/on/auto remain supported. Companion commits carry only this dependency fix; #3189 still accepts dense streaming requests through complete-response fallback until #3190 enables incremental output. Existing CPU vocoder full-response fallback remains covered.

Full all-files pre-commit passed. Pinned-runtime GPU/host regressions: **416 passed, zero skipped**. New cases cover inherited defaults, explicit modes, round trips and explicit stages. Resolved config equivalence separately compares every field for Tiny/dense and all four mode selections against the corresponding prior branch; explicit configurations must remain unchanged. Controller integrated config collection lacked Torch and is not counted as passed.

## Protocol and valid reuse

See [plan](measurement-plan.json), [source identities/archive hashes](source-manifest.json), [reuse provenance](reused-controls.json). One dedicated H200, identical pinned image, model/data assets, observer and scorers are reused; no weights or environment reinstall. Full EN1088 c16 and ZH2020 c1; two seeds42/43 ABBA. First qualify default-off main → #3136 (ZH first, then fresh EN); then final #3190 non-streaming → streaming quality/failures, also ABBA for both languages. Each arm saves YAML, resolved defaults, private cold caches, native speed/quality reports, per-request SIM/IDs/audio hashes, capture logs and sampled memory.

The previously running main740 ZH A42 control already uses native MPS off, with unchanged source/image/GPU/assets/settings. Reuse was elected before its result finished. Preserve its original raw config, including old `candidate_commit` as comparison context; actual measured source is main740. Do not rewrite it as a new candidate measurement. Old queue is held while that control finishes quality, then terminated without starting an old-auto candidate. New GPU tests and candidate measurements start only after its container exits. Raw coverage/scoring/costs must be verified before accepting reuse.

## First default-off results (incomplete ABBA)

Two completed ZH c1 arms are independently checked in [raw compact evidence](completed-results.tar.gz) and [verification](completed-arm-verification.json). B43 and A43 remain pending: these per-arm values are **not** a complete two-seed paired aggregate or a quality acceptance claim. Actual log timestamps preserve the predeclared order; every completed arm uses MPS off.

| Arm / actual source | req/s | WER % | SIM | Failures | Startup s | Observed peak GiB | Capture events |
| --- | ---: | ---: | ---: | --- | ---: | ---: | ---: |
| paired-zh-c1-A42 / `74003d00` | 0.957 | 0.626981 | 0.780467 | 0/2020 | 94.115 | 107.4209 | 19 |
| paired-zh-c1-B42 / `78d8c310` | 3.446 | 0.638811 | 0.780610 | 0/2020 | 148.175 | 108.2959 | 430 |

The candidate has 5 more ASR edits in this seed (265 → 270 / 42,266 units); preserve the adverse WER direction while awaiting seed43 and the second control. SIM increases in this single seed. Raw-main quality includes its known sampling-storage lifetime bug; optimization-only attribution is not assumed. Main exposes **0/2020** stop reasons, while this candidate exposes **2020/2020 stop**, with zero observed length limits. Unknown main reasons are not proof that no request reached a limit. Raw observed counts are preserved per arm and will be retained per seed in complete aggregates.

## Historical optional MPS on

The [prior source record](../v2/report.md) retains the completed EN c16 ABBA on main740off → PR3136b6d7auto: mean req/s8.863→41.617 (+369.56%), WER1.075944%→0.996400%, CAM++SIM0.778832→0.776681, zero failures/2176 per side, audio3.945993→3.903199s. Startup94.1145→137.1715s; observed peak108.6943→109.6670GiB; successful capture events19→430. This is whole-candidate optional-MPS performance, not an isolated MPS benefit or default-off result. SIM regresses and output length differs. Main contains the sampling-storage lifetime correctness bug, so raw-main differences mix the fix with optimization effects.

The [complete earlier qualification and trajectories](../../ming-review-20261028/report.md) preserve earlier source identities, the full historical matrix, corrected-lifetime controls, repeated scoring, adverse deltas and ablations. They are not relabeled as current-head measurements. New actual-source default-off and integrated streaming corpus results remain pending. No quality margin was predeclared.

## Interpretation and storage limits

Means are matched-seed arithmetic means; p95 is a seed range. EN c16 and ZH c1 cannot form a cross-language geometric summary. Preserve failures and adverse WER/SIM changes. Finish-reason observability is separate from native token-cap counts; the raw-main non-stream WAV control did not expose stop reasons, whereas the new candidate does; retain the actual per-arm coverage. Native throughput reports lack absolute per-request timestamps for independent recomputation. Memory is observed maximum with actual raw poll gaps retained; successful capture events need not be unique resident graphs.

Minimal result/score/request/hash/cost evidence is continuously backed up to private controller scratch; WAVs, weights and runtime caches remain on the node and are excluded. Source SHA and runtime probes are verified. Public provenance excludes private assignment/authentication files. Current-head Omni CI runs are [#3136](https://github.com/sgl-project/sglang-omni/actions/runs/41235981255), [#3189](https://github.com/sgl-project/sglang-omni/actions/runs/41235989382), [#3190](https://github.com/sgl-project/sglang-omni/actions/runs/41236000842). All three gates/preflights passed. Existing labels select PR Test plus Higgs MPS for #3136 (`examples/mps_dp/configs/higgs_h100_dp3.yaml`), and PR Test only for #3189/#3190. Other model stages were not selected. PR Test runs after successful setup for any selected stage, even when the resolver-specific `run_unit_test` flag is false. Shared setup passed on all three current heads; PR Test partitions are running or queued, and model stages remain pending. #3190 accelerator subsequently passed **1214 cases / 31 skipped**. Actual checkout `a6549eaef6cc4a0d790ce7a4e1bf0e753e49e632`, tree `66b5237126b03481b98668135242b0c0c5c8d913`, differs from the measured head by exactly the previously audited main740 → main3cb3 Ming-ASR #2977 patch. The three added skips are optional Ming-ASR checkpoint batch cases; the previous 28 skip identities remain. This is a synthetic integration checkout, not an identical head tree. Its main-only cookbook update is not a PR docs change: freshly fetched PR file lists remain 17/15/2, all doc/docs-free. CPU partitions, other PR units and model stages remain pending; no complete CI pass is claimed. Exact head identities and parsed preflight are saved alongside this report. Original PR bodies and all three head identities were read back after publication; [maintainer-thread reply](https://github.com/sgl-project/sglang-omni/pull/3136#discussion_r4433076884). CI and human review must be verified separately before landing the qualified prefix.

Developed through [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) in [OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index), with co-author [Ethan Feng](https://yichenfeng.me/).
