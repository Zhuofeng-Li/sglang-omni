Per-cohort startup-to-ready, sampled peak device memory and successful CUDA capture calls (seed42/43; main → PR). Capture calls include segmented prefill captures; they are not unique shape counts. No pooled quantiles or inferred unmeasured costs.

| Mode / c | Startup s | Peak GiB | Successful captures | Live captures after scoring | Capture delta |
| --- | --- | --- | --- | --- | --- |
| nonstream / 1 | 75.72/75.77 → 74.58/76.08 | 70.80/70.79 → 70.79/70.79 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
| nonstream / 16 | 77.09/78.59 → 82.11/82.60 | 71.60/71.58 → 71.27/71.42 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
| nonstream / 32 | 77.74/78.61 → 77.60/78.26 | 71.46/71.61 → 71.46/71.60 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
| stream / 1 | 75.60/76.73 → 76.16/75.66 | 70.80/70.79 → 70.79/70.79 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
| stream / 16 | 79.11/77.33 → 78.61/78.11 | 71.43/71.75 → 71.62/71.42 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
| stream / 32 | 78.61/83.14 → 78.16/78.11 | 71.76/71.78 → 71.46/71.46 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
