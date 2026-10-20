Prepared candidate `27216ebd18056a57406510b8588e351683d03d00` vs frozen main `2d5de98cd92b17df7974ac2ef4192b4a99263845`.

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
| 1 | 1.312 → 1.445 | +10.06% | 0.764/0.759 → 0.692/0.692 | 0.958/0.953 → 0.875/0.874 | N/A → N/A | N/A → N/A | 2.1268/1.5239 → 2.1268/1.5323 | 68.8625/68.9369 → 68.8625/68.9369 | 0/2176 → 0/2176 |
| 64 | 21.693 → 34.593 | +59.47% | 2.882/2.884 → 1.789/1.815 | 3.705/3.693 → 2.276/2.323 | N/A → N/A | N/A → N/A | 2.0012/1.4820 → 2.2440/1.4485 | 69.0790/68.7178 → 69.0550/68.8304 | 0/2176 → 0/2176 |

### Streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | --- |
| 1 | N/A: EN-only workload |
| 16 | N/A: historical EN-only workload |
| 32 | N/A: outside requested EN-only backfill |
| 64 | N/A: EN-only workload |

| c | EN req/s (main → PR) | Change | Mean response s | P95 response s | First audio mean s | First audio P95 s | WER % | SIM ×100 | Failed/attempted |
| ---: | ---: | ---: | --- | --- | --- | --- | --- | --- | --- |
| 1 | 1.259 → 1.341 | +6.55% | 0.787/0.801 → 0.741/0.750 | 0.987/1.008 → 0.933/0.945 | 0.3402/0.3468 → 0.3215/0.3269 | 0.3608/0.3756 → 0.3447/0.3533 | 2.1351/1.4988 → 2.1351/1.4988 | 68.8625/68.9310 → 68.8625/68.9310 | 0/2176 → 0/2176 |
| 64 | 15.552 → 14.910 | -4.13% | 4.022/4.056 → 4.231/4.276 | 5.194/5.223 → 4.934/4.994 | 2.1421/2.1433 → 3.3379/3.3507 | 2.6327/2.5321 → 3.9507/3.9567 | 2.3110/1.6495 → 2.1435/1.5741 | 69.1462/68.8226 → 68.9304/68.9033 | 0/2176 → 0/2176 |

Token-cap hits and finish-reason observation counts are retained in the per-seed JSON. Missing observed finish reasons cannot establish absence of truncation. No outliers are removed.
