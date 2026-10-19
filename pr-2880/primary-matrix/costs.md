Per-cohort startup-to-ready, sampled peak device memory and successful CUDA capture calls (seed42/43; main → PR). Capture calls include segmented prefill captures; they are not unique shape counts. No pooled quantiles or inferred unmeasured costs.

| Mode / c | Startup s | Peak GiB | Successful captures | Live captures after scoring | Capture delta |
| --- | --- | --- | --- | --- | --- |
| nonstream / 1 | 76.75/75.58 → 77.18/77.60 | 70.80/70.79 → 70.78/70.77 | 1468/1468 → 121/121 | 1468/1468 → 121/121 | -1347/-1347 |
| nonstream / 16 | 76.33/77.07 → 77.28/77.08 | 71.45/71.42 → 71.45/71.74 | 1468/1468 → 136/136 | 1468/1468 → 136/136 | -1332/-1332 |
| stream / 1 | 76.11/76.13 → 77.10/78.10 | 70.80/70.79 → 70.78/70.77 | 1468/1468 → 121/121 | 1468/1468 → 121/121 | -1347/-1347 |
