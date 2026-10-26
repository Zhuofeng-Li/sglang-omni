# Ming3 Tiny non-streaming: C24 qualification

Latest integrated-source coverage: **32/32 verified**. All EN/ZH c1/c16/c32/c64 two-seed ABBA blocks are complete. Earlier sections preserve historical snapshots and do not establish current publication readiness.

**Frozen matrix complete; publication pending. This remains a local unpublished draft.** All28 supplementary arms plus the original4 English c16 arms complete Tiny non-streaming EN/ZH × concurrency1/16/32/64 × two-seed ABBA (32 valid arms). The last arm finished2026-10-24 23:59:44UTC; off-node verification finishedOct25UTC. Replicated ENc64 p95/RTF, ZHc32 p99/RTF p99 and ZHc64 RTFp99 regressions remain publication blockers. Every request and the frozen16-request warmup remain unchanged. Rebuilt pinned-runtime frozen-head GPU regressions passed2026-10-25UTC (208 passed, six unsupported four-row-tile shape skips; actual CUDA identity/arithmetic probe passed). Causal EN c64 two-seed ABBA is complete: reducing preprocessing workers4→1 lost21.54% mean req/s and worsened p95/p99 on both seeds, so it was rejected. A separate synthetic KDA probe isolated18.16s of first-call large-grid compilation versus0.9ms on repeat, with bitwise repeat equality and unchanged RNG; this is a kernel diagnostic, not a final end-to-end repair result. Startup repair, affected final-head qualification and resolution of partially overlapping open PR #3136 remain pending. The full diagnostic quality scores include the seed43 long-output outliers without dropping or replacing requests. See [complete paired matrix and costs](complete-matrix-summary.json) and [supplementary per-arm measurements](supplementary-metrics.json).

This report contains sanitized implementation and measurement evidence. The originating research trajectory remains private; no agent session, transcript, input corpus, credential, or audio is published here.

Measured main: `0ee9d47dffe16a5b1cc8d1dcbfbb04769884107f`. Measured candidate: `97f47d2c45286b09adf87ea6acf0054a9b2325de`. Frozen supplementary candidate: `bdfca67f9931a10218835f556815d1834b9fbfd4` (one subsequent test-only addition). Observed upstream: `6b6329afb04960b0f595f674d87f94934243c007` at 2026-10-24T23:07:07.010713+00:00; affected runtime, shared scheduling, dependency and active benchmark paths are unchanged from the measured main.

## Original English c16 protocol and results

Single H200, English Seed-TTS 1088 rows, concurrency 16. See [configuration](configuration.json) for exact revisions, limits, seed/order, cache boundaries and runtime versions. Successful order: A42, B42, B43, A43. A is clean main; B is the combined C24 patch. Each arm includes native and authoritative ASR and all 1088 CAM++ similarity pairs.

| Arm | req/s | Mean latency (s) | p95 latency (s) | WER (%) | CAM++ cosine | Startup (s) | Peak GiB | Captures |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| A42 | 5.721 | 2.775 | 3.989 | 2.2691 | 0.81476 | 112.115 | 109.263 | 19 |
| B42 | 10.886 | 1.461 | 2.141 | 1.1220 | 0.82390 | 174.177 | 108.823 | 280 |
| B43 | 10.970 | 1.453 | 2.193 | 1.1052 | 0.82452 | 174.198 | 109.228 | 280 |
| A43 | 5.665 | 2.809 | 3.918 | 2.0347 | 0.81407 | 108.114 | 108.198 | 19 |

Throughput: **5.693 → 10.928 req/s (+91.96%)**. Audio throughput: **23.035 → 39.334 audio-s/s (+70.76%)**. Mean generated duration: 4.046 → 3.599 s (-11.05%). The request-throughput change includes this duration difference; no whole-serving waveform identity is claimed.

Aggregate WER: 2.1519% → 1.1136%. Aggregate CAM++ cosine: 0.81442 → 0.82421. Each arm has0 failed/1088 attempted TTS requests (2176 per branch across two seeds). All11 original English c16 task-style paired guards pass; this does not establish full-matrix publication readiness. Raw aggregate records are in [metrics](metrics.json), and [WER counts](wer-counts.json) permit exact corpus-WER recomputation.

Startup is the arithmetic mean across seeds, measured from server launch to readiness with weights already cached. Peak device memory is the maximum 1-second NVML observation during TTS across seeds; the small negative memory delta is not evidence of memory savings. Capture counts are successful PyTorch capture completions during TTS, excluding ASR. Per-seed p95 values remain separate; the PR reports their range rather than an average or invented pooled percentile.

## Incomplete attempts and operational corrections

One initial A42 invocation completed native generation/ASR but failed a separate driver metadata lookup (`stream` was omitted); it was excluded and the complete block restarted before any valid paired arm was collected. Two B43 invocations generated all audio but failed the unchanged native client's subsequent ASR port bind. Both were retained and excluded from complete-pair statistics. [Incomplete attempts](incomplete-attempts.json) retains their available TTS summaries.

The operator's cleanup wrapper now waits after native server shutdown for the port to actually become bindable. FIN_WAIT2 was observed and cleared after 13.852 seconds. It preserves the original bind check and does not change inputs, inference, timing collection or scoring. The successful A42/B42 arms needed no such wait and remain reusable. All 19 frozen evaluator files have their original hashes.

## Implementation and validation

The [patch](implementation.patch) combines request noise-storage reuse, denser acoustic graph buckets, cached timestep/rotary work, packed projections, native-rounding normalization, four preprocessing workers, and exact-length Tiny vocoder graphs. Triton is optional; custom reductions are restricted to the validated CUDA/PyTorch version and layouts. Existing eager/native and gradient paths remain available. Full code and tensor tests: 207 passed, six unsupported-shape skips, then four final vocoder-module tests passed including the added real-CUDA ownership/fallback regression. Full repository pre-commit passed.

The section above preserves the original Tiny non-streaming English c16 evidence, measured2026-10-23UTC; the frozen supplementary EN/ZH c1/c16/c32/c64 matrix is complete, while regression-fix qualification and overlap resolution remain pending as recorded above. Streaming and Dense are explicit scope exclusions. CI stage/model labels have not been selected for publication: reread the latest target guide/resolver/workflows and live labels, then verify actual preflight/run and revision. Previous label observations are historical.

The historical C24 trajectory measured 5.7263 → 10.8767 req/s against its original base, using three sequential seeds; that history is not substituted for this paired qualification. Prepared from an autonomous research run using [RSI-Harness](https://github.com/OpenRSI-Foundation/OpenRSI-Index/tree/main/RSI-Harness) and [OpenRSI-Index](https://github.com/OpenRSI-Foundation/OpenRSI-Index).

## Local startup repair validation (2026-10-25UTC)

The unpublished warmup repair at faa6286, based on actual main58c4ebb, passed full pre-commit and215 GPU tests (six unsupported-shape skips); CPU-only imports passed for both clean main and repair. One complete EN1088/c64/seed42 candidate smoke completed with zero failures/skips:18.687req/s, p95=5.070s, p99=6.206s, word WER=1.2476%, CAM++SIM=0.823399. No new KDA kernel was compiled during formal requests. Startup was250.239s, including76.17s KDA warmup; sampled TTS peak113693MiB,280 captures. This is not a paired-main gain or final publication qualification. All requests are retained; this seed produced no20-second output. See [smoke metrics](repair-smoke.json) and [unpublished repair patch](warmup-repair.patch).

## Integrated Tiny smoke on selected main

On October 25, 2026 UTC, candidate `6b871400ce1a71444049cc4a3e9d0c10bc2803d6` integrated the remaining Tiny changes with the unmerged PR #3136 prerequisite and selected main `58c4ebbd4a63f6bd1452346675b4d7e017b88c24`. All 1088 EN c64/seed42 TTS, WAV, ASR and speaker pairs completed without failures/skips. Candidate-only throughput was 23.066 req/s, mean/p95/p99 latency 2.734/4.275/5.407 seconds, word WER 145/11943 (1.2141%) and CAM++ cosine 0.822565. These are a single smoke, not paired-main benefit.

Startup was 252.235 seconds including 76.45 seconds of KDA prewarming; peak sampled TTS memory was 114295 MiB and 284 successful graphs were observed. No costly KDA intra/inter variants compiled during formal requests, but one shared KDA state variant did: compilation has not been eliminated from the full KDA call graph. All requests, including cold requests, remain in the percentiles. Full clean-main EN/ZH c1/16/32/64 two-seed ABBA qualification is now running; PR publication remains pending. See [sanitized integrated smoke](integrated-smoke.json).

## Integrated EN64 paired result

The integrated6b87140 candidate versus clean58c4 main completed EN64 A42/B42/B43/A43 on October25UTC, with1088 requests per arm and no failures/skips. Mean throughput was10.4105→22.7895req/s (+118.91%); p95 seed ranges8.378–8.693→4.517–4.703s and p99 ranges29.227–29.709→6.039–6.611s. Word WER2.6920→1.1597%, CAM++ cosine0.8119→0.8240. All tail metrics improved in both seeds. The mean output-duration change and audio throughput are retained in the [complete EN64 result](integrated-en-c64.json).

Mean startup107.605→255.760s (+148.155s), maximum TTS NVML111923→114295MiB (+2372MiB), successful captures19→284 (+265). This measures the bundle including the unmerged PR3136 prerequisite and does not isolate the Tiny-only contribution. The other seven cells and publication/dependency audit remain pending.

## Integrated bilingual c64 result

EN64 and ZH64 both completed the two-seed A42/B42/B43/A43 protocol on clean main58c4 versus integrated candidate6b87140. All8 arms, 12432 TTS/WAV/ASR/speaker pairs, completed with no failures/skips and passed source/device/image/quality/cost evidence verification. Bilingual geometric throughput improved115.08% (EN118.91%, ZH111.33%). All recorded latency/RTF tails improved in both seeds in both languages. This measures the bundle including unmergedPR3136, not an isolated Tiny-only component.

ZH64 throughput8.6445→18.2680req/s, ZH character error rate4.0150→2.0797%, CAM++ cosine0.8279→0.8397. Its RTFp99 seed range1.5129–1.5284→0.9272–0.9739. Output-duration changes, audio throughput, startup/memory/graph costs, per-seed records and hashes are in [complete bilingualc64 evidence](integrated-c64-paired.json). The other24 c1/c16/c32 arms and final dependency/publication/CI/review/merge checks remain pending.

## Integrated EN/ZH c16 paired update (2026-10-26 UTC)

[Complete sanitized c16 paired records](integrated-c16-paired.json) retain both seeds, hashes and costs. EN throughput changes +117.57%, ZH +105.39%; bilingual geometric change is +111.39%. ZH16 is complete in ABBA order, all 2020 requests per arm with no failures/skips. Latency p99 seed ranges are 5.421–11.689 → 2.544–2.599 s; RTF p99 ranges are 0.6806–0.6873 → 0.3731–0.3911. All recorded tail metrics improve in both seeds. Mean output duration changes 5.7372 → 5.5601 s (-3.09%); audio throughput changes 26.7880 → 53.3230 audio-s/s (+99.06%). Request gains include this duration change. Seed 43 SIM decreases 0.842155 → 0.841444 (-0.000711), despite the two-seed mean increasing; retain this quality difference. Startup increases147.124 s, peak TTS memory increases3024 MiB and successful graph captures increase265 for ZH16. These are combined integrated-bundle measurements; the complete32-arm gate remains pending.

## Integrated EN c1 paired update (2026-10-26 UTC)

[Complete sanitized EN c1 paired records](integrated-en-c1.json) retain both seeds, raw-evidence hashes, costs and the matched long-output proof. EN1 is complete in ABBA order, all 1088 requests per arm with no failures/skips. Latency p99 seed ranges are 2.054–2.122 → 0.892–0.913 s; RTF p99 ranges are 0.4007–0.4032 → 0.1943–0.1984. All recorded tail metrics improve in both seeds. Matched-seed corpus WER and mean SIM are identical in each seed, and mean output duration stays 3.6001 s. Audio throughput changes 2.8920 → 6.4215 audio-s/s (+122.04%). A seed 43 output reaches 20.0 s and contributes 90 insertion errors; its baseline/candidate WAV hashes are identical and it remains in both complete scores. ZH1 remains pending, so no bilingual c1 aggregate is reported. Startup increases149.605 s, peak TTS memory increases2968 MiB and successful graph captures increase265. These remain combined-bundle measurements; the32-arm publication gate is incomplete.

## ZH1 infrastructure retry (2026-10-26 UTC)

The first ZH1/A42 attempt stopped after1026/2020 generated requests when external shared CPU load peaked at7.16668069 cores, above the unchanged2-core evaluator guard; sampler errors were0. The controller archived this incomplete attempt and is waiting for the original four30-second idle windows before retrying. All28 prior verified arms remain intact. This attempt contributes no qualified performance/quality result; failure/config/command/dataset evidence and hashes are saved off-node. No workload source, scoring, limits or resource affinity has been changed.

The original CPU pool subsequently recovered, and the same controller passed all four original idle windows and launched ZH1/A42 attempt2. Configuration and both container/benchmark command records match the archived attempt exactly. The alternative-CPU survey was not deployed and no additional GPU was allocated. The replacement reruns all2020 rows; the incomplete attempt is never spliced into a qualified arm.

ZH1/A42 replacement attempt2 is now independently verified off-node:2020 TTS/WAV/ASR/speaker pairs, zero failed/skipped. Its raw invalid-attempt exclusion hash matches the preserved failure file. [Infrastructure recovery and replacement evidence](integrated-infrastructure-attempts.json) retains the diagnosed CPU failure and the complete replacement results; only the qualified full replacement contributes to metrics. Coverage is29/32; the other three ZH1 arms remain pending.

## ZH1 candidate seed42 completion (2026-10-26 UTC)

ZH1/B42 attempt1 passed independent off-node verification of all2020 TTS/WAV/native and authoritative ASR/speaker pairs, zero failed/skipped. Throughput is1.221req/s, mean latency0.819s, p951.063s, p991.252s and RTFp990.1635; character errors937/42266 (864 substitutions,19 deletions,54 insertions), SIM0.8381820259. Startup254.291s, peak TTS memory111747MiB,284 successful graphs. This is one arm of the incomplete two-seed ABBA cell; no complete ZH1 or bilingual c1 gain is claimed. Coverage is30/32; ZH1/B43 and A43 remain pending. [Sanitized ZH1 progress receipts](integrated-zh-c1-progress.json) preserve both verified seed42 arms and raw-evidence hashes.

## Complete integrated matrix (2026-10-26 UTC)

[Complete sanitized paired matrix](integrated-complete-matrix.json) includes all32 verified arms,49,728 qualified requests, source/result hashes and costs. Bilingual throughput changes at c1/c16/c32/c64 are +124.62%/+111.39%/+114.32%/+115.08%. These are combined candidate results including unmerged prerequisite3136, not the independent benefit of the19-file Tiny increment. All recorded latency/RTF tails improve in both seeds; ZH16 seed43 SIM decreases0.000711 and remains disclosed. Full ZH1 records are in [ZH1 paired evidence](integrated-zh-c1.json). All32 raw receipt hashes were rechecked off-node and the exact Radix assignment was released; no live consumers remained. Draft publication and current-main/dependency/CI checks are separate gates.

## Exact review-head CI (2026-10-26 UTC)

[Sanitized head CI receipt](ci-head-validation.json) records manual workflow40333279462 on99c78ed53d860cb2296cf2517809fd15ddf500ad: CPU A4270 passed/61 skipped, CPU B5200 passed/38 skipped, accelerator1006 passed/28 skipped. The requested unit-only preflight and exact source were verified, and environment cleanup succeeded. Automatic lint/docs/Rust/testlayout/playback and bothNPUimagebuilds passed. These results do not clear the draftPRgate or validate finalmain integration; prerequisite3136 remains unmerged.
