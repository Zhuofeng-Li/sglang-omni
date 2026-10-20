Per-cohort costs (seed42/43; main → PR). Startup is launch-to-health-ready, peak memory is sampled every 0.5 s, and graph counts are successful capture events rather than unique shapes or post-shutdown live objects.

| Mode / c | Startup s | Peak GiB | Successful captures | Capture delta |
| --- | --- | --- | --- | --- |
| nonstream / 1 | 115.11/112.10 → 153.14/153.14 | 66.86/66.86 → 70.42/70.42 | 152/152 → 19236/19236 | 19084/19084 |
| nonstream / 64 | 116.11/116.11 → 157.14/159.14 | 67.33/67.31 → 70.96/70.95 | 152/152 → 19236/19236 | 19084/19084 |
| stream / 1 | 113.10/117.11 → 152.14/162.15 | 66.73/66.73 → 70.42/70.42 | 152/152 → 19236/19236 | 19084/19084 |
| stream / 64 | 114.10/113.10 → 156.14/153.14 | 67.35/67.30 → 70.72/70.77 | 152/152 → 19236/19236 | 19084/19084 |
