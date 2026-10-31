# Ming3 refreshed final integration — main 74003d00

> Historical qualification notice: Historical optional-MPS-on qualification; stopped after the maintainer requested inherited default MPS off. The completed EN block below is main off → candidate auto, not the new default-off performance. See [active default-off qualification](../v3/report.md).
Status: superseded by the maintainer-requested default-MPS-off qualification after four EN arms and one unchanged clean-main ZH control finished. Five completed arms are verified in [raw compact evidence](completed-results.tar.gz). No final full-qualification pass is claimed.

Main #3355 changes the exact small CPU latent stream transport used by Ming, plus shared receive-lane scheduling. The stack was merged with actual main `74003d00f53e7f1a05593b556f21a31760a6fab6`, preserving all optimization and fallback changes. Refreshed heads: #3136 `b6d7dbc51360bf6c4a1e6f44976802c20967dcb3`, #3189 `8b432a47fb5afdcaf98892174e73201055e2d4bd`, #3190 `90fafa93b786011801a0ae5aecb5fac7ea773c47`.

Both individual and cumulative source diffs are checked; GitHub now reports current base snapshots and exact file counts 16 / 15 / 2, with no documentation-directory changes. Draft #3217 remains excluded from landing. Full pre-commit passed without modifications. The exact new integrated source passed **404 GPU/host cases, zero skipped**, including Ming and shared packed-stream/stage routing regressions. The post-test CUDA IPC producer warning is retained in the log; the test process exited successfully and its container ended before benchmark startup.

The H200 assignment, exact runtime image, pinned model/dataset assets and observer are reused from the [earlier qualification](../report.md). New source archives and runtime import/GPU UUID are verified. No model weights or environment were downloaded again. The same 16-arm compact EN c16 / ZH c1 protocol uses two-seed ABBA, full corpora, actual main → #3136 and final #3190 non-streaming → streaming, with fresh per-arm compilation/reference caches. Earlier source measurements are preserved, never relabeled as new main or new head results.

The old queue was held at an arm boundary, its active full quality evaluation allowed to finish, and then stopped. Five completed prior-source arms are verified and archived on the controller. That record includes EN c16 ABBA and one ZH main seed; remaining old-source arms were superseded. This refreshed queue was subsequently stopped at an arm boundary for the MPS-default review; the active v3 queue is linked above.

New current-head CI runs: #3136 41229499606, #3189 41229519708, #3190 41229537572. All three subsequently passed their selected units/accelerator; #3136 also passed its explicitly selected Higgs MPS job and cleanup, as recorded in the verification files. They qualify these historical heads only. Previous-head CI passes are historical. Full new-head paired results, exact CI checkout/preflight and human review remain pending. This is an incomplete historical-source record, not a completed final experiment report.

## Completed EN c16 paired block

Actual main74003d00 → PR3136b6d7dbc5; A42 B42 B43 A43, 1088 requests/arm. Arithmetic seed means: req/s **8.863 → 41.617 (+369.56%)**; latency mean **1.7955 → 0.3805 s**, seed p95 range **2.675–2.690 → 0.526–0.526 s**; corpus WER **1.075944% → 0.996400%**; CAM++ SIM **0.778832 → 0.776681**. Failed requests **0/2176 → 0/2176**. Audio duration mean **3.945993 → 3.903199 s (-1.08%)**. Output tokens by seed: main54024/53307, PR53451/52716.

Startup means **94.1145 → 137.1715 s (+43.057 s)**. Sampled device memory peaks by seed: main108.6943/108.6943 GiB, PR108.8232/109.6670 GiB. Successful capture_end events:19 →430 per seed. Raw samples/logs/event counts and scoring arithmetic are verified in the off-node result archive. Capture events are not necessarily unique resident graphs; memory is the observed sampled maximum. No quality acceptance margin or pure-optimization attribution is assumed; actual main still has the sampling-scale lifetime bug discussed in the earlier evidence. Native finish-reason observability is recorded separately from the native token-cap counter.

ZH c1 and final-head streaming/non-streaming blocks remain pending. Different EN/ZH concurrency cells do not produce a geometric throughput summary.
