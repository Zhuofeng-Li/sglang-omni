# Ming3 final review: inherited default MPS off

Updated 2026-10-31T19:48:27.689990+00:00. Qualification is incomplete; no merge-readiness claim.

## Source and review fixes

Frozen main `74003d00f53e7f1a05593b556f21a31760a6fab6`; #3136 `78d8c310a65c14dd4bceb87e220c8304917805bb`, #3189 `35bf42ec695da774d6e1cf8731c70b291d671af9`, #3190 `2a636231d688b7bc83d78769e4f5162502680675`. Main #3355 is integrated. Later `3cb3c6cc` changes Ming-ASR only and was audited separately from Ming3-TTS and the Qwen3-ASR scorer. Draft #3217 is excluded. Full individual diffs have 17/15/2 files and no doc/docs changes.

[Maintainer review](https://github.com/sgl-project/sglang-omni/pull/3136#discussion_r4432962390) requests shared default `mps: off` for Tiny and dense. The model override and redundant field are removed. Explicit off/on/auto remain supported. Companion commits carry only this dependency fix; #3189 still accepts dense streaming requests through complete-response fallback until #3190 enables incremental output. Existing CPU vocoder full-response fallback remains covered.

Full all-files pre-commit passed. Pinned-runtime GPU/host regressions: **416 passed, zero skipped**. New cases cover inherited defaults, explicit modes, round trips and explicit stages. Resolved config equivalence separately compares every field for Tiny/dense and all four mode selections against the corresponding prior branch; explicit configurations must remain unchanged. Controller integrated config collection lacked Torch and is not counted as passed.

## Protocol and valid reuse

See [plan](measurement-plan.json), [source identities/archive hashes](source-manifest.json), [reuse provenance](reused-controls.json). One dedicated H200, identical pinned image, model/data assets, observer and scorers are reused; no weights or environment reinstall. Full EN1088 c16 and ZH2020 c1; two seeds42/43 ABBA. First qualify default-off main → #3136 (ZH first, then fresh EN); then final #3190 non-streaming → streaming quality/failures, also ABBA for both languages. Each arm saves YAML, resolved defaults, private cold caches, native speed/quality reports, per-request SIM/IDs/audio hashes, capture logs and sampled memory.

The previously running main740 ZH A42 control already uses native MPS off, with unchanged source/image/GPU/assets/settings. Reuse was elected before its result finished. Preserve its original raw config, including old `candidate_commit` as comparison context; actual measured source is main740. Do not rewrite it as a new candidate measurement. Old queue is held while that control finishes quality, then terminated without starting an old-auto candidate. New GPU tests and candidate measurements start only after its container exits. Raw coverage/scoring/costs must be verified before accepting reuse.

## Historical optional MPS on

The [prior source record](../v2/report.md) retains the completed EN c16 ABBA on main740off → PR3136b6d7auto: mean req/s8.863→41.617 (+369.56%), WER1.075944%→0.996400%, CAM++SIM0.778832→0.776681, zero failures/2176 per side, audio3.945993→3.903199s. Startup94.1145→137.1715s; observed peak108.6943→109.6670GiB; successful capture events19→430. This is whole-candidate optional-MPS performance, not an isolated MPS benefit or default-off result. SIM regresses and output length differs. Main contains the sampling-storage lifetime correctness bug, so raw-main differences mix the fix with optimization effects.

The [complete earlier qualification and trajectories](../../ming-review-20261028/report.md) preserve earlier source identities, the full historical matrix, corrected-lifetime controls, repeated scoring, adverse deltas and ablations. They are not relabeled as current-head measurements. New actual-source default-off and integrated streaming corpus results remain pending. No quality margin was predeclared.

## Interpretation and storage limits

Means are matched-seed arithmetic means; p95 is a seed range. EN c16 and ZH c1 cannot form a cross-language geometric summary. Preserve failures and adverse WER/SIM changes. Finish-reason observability is separate from native token-cap counts; non-stream WAV responses did not expose stop reasons. Native throughput reports lack absolute per-request timestamps for independent recomputation. Memory is observed maximum with actual raw poll gaps retained; successful capture events need not be unique resident graphs.

Minimal result/score/request/hash/cost evidence is continuously backed up to private controller scratch; WAVs, weights and runtime caches remain on the node and are excluded. Source SHA and runtime probes are verified. Public provenance excludes private assignment/authentication files. Current-head CI and human review must be verified separately before landing the qualified prefix.

Developed through [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) in [OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index), with co-author [Ethan Feng](https://yichenfeng.me/).
