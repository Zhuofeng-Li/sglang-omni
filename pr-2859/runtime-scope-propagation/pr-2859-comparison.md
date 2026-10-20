Prepared candidate `2c7610e9d236feb285522df1590e0ef6d0800ed7` vs frozen main `2d5de98cd92b17df7974ac2ef4192b4a99263845`.

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
| 64 | 21.634 → 34.379 | +58.91% | 2.902/2.880 → 1.823/1.805 | 3.694/3.663 → 2.316/2.272 | N/A → N/A | N/A → N/A | 2.1100/1.5490 → 2.2356/1.4988 | 69.0730/68.9154 → 69.0655/68.8165 | 0/2176 → 0/2176 |

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
| 64 | 15.384 → 20.431 | +32.80% | 4.078/4.077 → 3.037/3.078 | 5.215/5.220 → 4.058/3.968 | 2.1480/2.1394 → 1.7849/1.8120 | 2.5306/2.4988 → 2.6251/2.4501 | 2.2356/1.5490 → 2.2021/1.4569 | 69.0733/68.9383 → 69.0767/68.8243 | 0/2176 → 0/2176 |

Token-cap hits and finish-reason observation counts are retained in the per-seed JSON. Missing observed finish reasons cannot establish absence of truncation. No outliers are removed.
