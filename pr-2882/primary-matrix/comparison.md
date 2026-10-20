Candidate `2cad178053585b41d486c1584796d58b205541a0` vs frozen main `2d5de98cd92b17df7974ac2ef4192b4a99263845`.

H100 80GB, SeedTTS EN (1088) / ZH (2020), seeds 42/43; each block runs main(42) → PR(42) → PR(43) → main(43). Throughput and mean latency are arithmetic means across the two seeds. P95, first-text latency and corpus WER retain seed42/43 values. Geometric change uses the ratio of mean req/s for each language, followed by the geometric mean of the two language ratios. Missing or incompletely paired blocks remain Pending. ASR SIM is N/A because the output is text.

### Non-streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | +1.37% |
| 16 | -0.52% |
| 32 | Pending |
| 64 | Pending |

Detailed metrics (main → PR; slash-separated values retain seed42/43):

| c / split | req/s | Mean response ms | P95 response ms | First-text mean ms | First-text P95 ms | WER % | Failed/attempted |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| 1 / EN | 24.584 → 24.854 | 40.53 → 40.09 | 49.24/49.61 → 49.34/48.79 | N/A → N/A | N/A → N/A | 1.2258/1.2258 → 1.2258/1.2258 | 0/2176 → 0/2176 |
| 1 / ZH | 27.266 → 27.712 | 36.53 → 35.95 | 46.11/46.72 → 46.27/45.24 | N/A → N/A | N/A → N/A | 0.5933/0.5933 → 0.5933/0.5933 | 0/4040 → 0/4040 |
| 16 / EN | 149.267 → 147.654 | 106.39 → 107.65 | 138.76/140.55 → 141.96/142.46 | N/A → N/A | N/A → N/A | 1.2031/1.2107 → 1.2031/1.2031 | 0/2176 → 0/2176 |
| 16 / ZH | 155.648 → 155.718 | 102.20 → 102.07 | 138.03/138.85 → 138.65/138.32 | N/A → N/A | N/A → N/A | 0.5904/0.6023 → 0.5993/0.5993 | 0/4040 → 0/4040 |

### Streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | +1.53% |
| 16 | Pending |
| 32 | Pending |
| 64 | Pending |

Detailed metrics (main → PR; slash-separated values retain seed42/43):

| c / split | req/s | Mean response ms | P95 response ms | First-text mean ms | First-text P95 ms | WER % | Failed/attempted |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| 1 / EN | 24.744 → 24.844 | 40.26 → 40.10 | 49.29/49.40 → 49.27/49.55 | 11.70/12.00 → 11.50/11.40 | 12.80/13.60 → 13.20/13.20 | 1.2258/1.2258 → 1.2258/1.2258 | 0/2176 → 0/2176 |
| 1 / ZH | 26.947 → 27.668 | 36.96 → 36.00 | 47.14/46.81 → 45.17/46.62 | 11.80/11.90 → 11.00/11.30 | 13.00/13.20 → 11.80/12.60 | 0.5933/0.5933 → 0.5933/0.5933 | 0/4040 → 0/4040 |
