Per-cohort costs (seed42/43; main → PR). Startup is launch-to-health-ready, peak memory is sampled every 0.5 s, and graph counts are successful capture events rather than unique shapes or post-shutdown live objects.

| Mode / c | Startup s | Peak GiB | Successful captures | Capture delta |
| --- | --- | --- | --- | --- |
| nonstream / 1 | 112.10/116.11 → 157.14/156.14 | 66.86/66.86 → 70.42/70.42 | 152/152 → 19236/19236 | 19084/19084 |
| nonstream / 64 | 113.10/113.11 → 154.11/153.13 | 67.23/67.33 → 71.03/71.05 | 152/152 → 19236/19236 | 19084/19084 |
| stream / 1 | 113.11/113.10 → 154.14/155.14 | 66.73/66.73 → 70.42/70.42 | 152/152 → 19236/19236 | 19084/19084 |
| stream / 64 | 112.10/113.10 → 152.13/152.14 | 67.27/67.32 → 70.82/70.86 | 152/152 → 19236/19236 | 19084/19084 |
