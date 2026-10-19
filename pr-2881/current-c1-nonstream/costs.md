Per-cohort startup-to-ready, sampled peak device memory and successful CUDA capture calls (seed42/43; main → PR). Capture calls include segmented prefill captures; they are not unique shape counts. No pooled quantiles or inferred unmeasured costs.

| Mode / c | Startup s | Peak GiB | Successful captures | Live captures after scoring | Capture delta |
| --- | --- | --- | --- | --- | --- |
| nonstream / 1 | 76.10/76.10 → 76.60/75.10 | 70.80/70.79 → 70.80/70.79 | 1468/1468 → 1468/1468 | 1468/1468 → 1468/1468 | 0/0 |
