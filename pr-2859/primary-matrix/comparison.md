Prepared candidate `757c09eb272079b6c08f88bcaa393ffe3845029a` vs frozen main `2d5de98cd92b17df7974ac2ef4192b4a99263845`.

Requested c1/c64 EN-only backfill: full 1088 requests per cohort, seeds 42/43 in main(42) → PR(42) → PR(43) → main(43) order. The req/s change uses arithmetic means across seeds. Slash-separated values retain seed42/43; percentiles are not pooled. Each displayed block requires completed generation, full WER/SIM scoring, matched settings/order, the assigned GPU and audited ABBA intervals. The bilingual geometric summary is N/A for this EN-only workload; historical c16 remains separate with its original source/date.

### Non-streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | --- |
| 1 | N/A: EN-only workload |
| 16 | N/A: historical EN-only workload |
| 32 | N/A: outside requested EN-only backfill |
| 64 | N/A: EN-only workload |

| c | EN req/s (main → PR) | Change | Mean response s | P95 response s | First audio mean s | First audio P95 s | WER % | SIM ×100 | Failed/attempted |
| ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1.313 → 1.440 | +9.59% | 0.760/0.763 → 0.694/0.695 | 0.953/0.958 → 0.873/0.875 | N/A → N/A | N/A → N/A | 2.1435/1.5155 → 2.1351/1.5155 | 68.8625/68.9369 → 68.8625/68.9369 | 0/2176 → 0/2176 |
| 64 | 22.229 → 34.688 | +56.05% | 2.822/2.809 → 1.805/1.798 | 3.596/3.590 → 2.305/2.296 | N/A → N/A | N/A → N/A | 2.2607/1.5239 → 2.2859/1.5825 | 69.0197/68.8522 → 69.0957/68.7288 | 0/2176 → 0/2176 |

### Streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | --- |
| 1 | N/A: EN-only workload |
| 16 | N/A: historical EN-only workload |
| 32 | N/A: outside requested EN-only backfill |
| 64 | N/A: EN-only workload |

| c | EN req/s (main → PR) | Change | Mean response s | P95 response s | First audio mean s | First audio P95 s | WER % | SIM ×100 | Failed/attempted |
| ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1.264 → 1.349 | +6.69% | 0.791/0.791 → 0.742/0.741 | 0.993/0.991 → 0.934/0.931 | 0.3414/0.3424 → 0.3222/0.3213 | 0.3619/0.3634 → 0.3458/0.3430 | 2.1268/1.5155 → 2.1268/1.5155 | 68.8625/68.9310 → 68.8625/68.9310 | 0/2176 → 0/2176 |
| 64 | 15.570 → 14.720 | -5.46% | 4.043/4.017 → 4.282/4.332 | 5.157/5.165 → 4.993/5.048 | 2.1391/2.1218 → 3.3843/3.4241 | 2.4460/2.4786 → 3.9724/4.0667 | 2.1770/1.5239 → 2.1770/1.6244 | 68.9019/68.8348 → 69.0635/68.8849 | 0/2176 → 0/2176 |

Token-cap hits and finish-reason observation counts are retained in the per-seed JSON. Missing observed finish reasons cannot establish absence of truncation. No outliers are removed.
