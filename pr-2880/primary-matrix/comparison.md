Candidate `67e28de826af967a9dec76506c91473e257aa156` vs frozen main `2d5de98cd92b17df7974ac2ef4192b4a99263845`.

H100 80GB, SeedTTS EN (1088) / ZH (2020), seeds 42/43; each block runs main(42) → PR(42) → PR(43) → main(43). Throughput and mean latency are arithmetic means across the two seeds. P95, first-text latency and corpus WER retain seed42/43 values. Geometric change uses the ratio of mean req/s for each language, followed by the geometric mean of the two language ratios. Missing or incompletely paired blocks remain Pending. ASR SIM is N/A because the output is text.

### Non-streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | +1.34% |
| 16 | +0.32% |
| 32 | Pending |
| 64 | Pending |

Detailed metrics (main → PR; slash-separated values retain seed42/43):

| c / split | req/s | Mean response ms | P95 response ms | First-text mean ms | First-text P95 ms | WER % | Failed/attempted |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| 1 / EN | 24.520 → 24.935 | 40.63 → 39.97 | 49.63/49.89 → 48.69/49.06 | N/A → N/A | N/A → N/A | 1.2258/1.2258 → 1.2258/1.2258 | 0/2176 → 0/2176 |
| 1 / ZH | 26.896 → 27.164 | 37.01 → 36.67 | 47.04/47.01 → 46.46/47.00 | N/A → N/A | N/A → N/A | 0.5933/0.5933 → 0.5933/0.5933 | 0/4040 → 0/4040 |
| 16 / EN | 148.344 → 149.407 | 107.14 → 106.27 | 140.49/140.10 → 138.74/143.46 | N/A → N/A | N/A → N/A | 1.2031/1.2031 → 1.2031/1.2031 | 0/2176 → 0/2176 |
| 16 / ZH | 155.129 → 155.002 | 101.87 → 101.94 | 138.20/137.57 → 136.92/138.22 | N/A → N/A | N/A → N/A | 0.5933/0.5874 → 0.5844/0.6023 | 0/4040 → 0/4040 |

### Streaming

| Concurrency | EN/ZH geometric throughput change |
| ---: | ---: |
| 1 | +2.07% |
| 16 | -1.02% |
| 32 | Pending |
| 64 | Pending |

Detailed metrics (main → PR; slash-separated values retain seed42/43):

| c / split | req/s | Mean response ms | P95 response ms | First-text mean ms | First-text P95 ms | WER % | Failed/attempted |
| --- | ---: | ---: | --- | --- | --- | --- | --- |
| 1 / EN | 24.375 → 24.876 | 40.87 → 40.07 | 50.10/49.72 → 49.14/49.29 | 12.40/12.20 → 11.70/11.70 | 14.10/14.00 → 13.10/13.50 | 1.2258/1.2258 → 1.2258/1.2258 | 0/2176 → 0/2176 |
| 1 / ZH | 26.745 → 27.300 | 37.21 → 36.48 | 47.28/47.36 → 46.81/46.07 | 12.10/11.90 → 11.70/11.40 | 13.40/13.50 → 12.70/12.50 | 0.5933/0.5933 → 0.5933/0.5933 | 0/4040 → 0/4040 |
| 16 / EN | 148.808 → 146.581 | 106.62 → 107.06 | 138.73/138.56 → 140.18/140.68 | 56.00/56.60 → 58.90/58.60 | 77.20/78.20 → 80.90/81.00 | 1.2107/1.2031 → 1.2031/1.2031 | 0/2176 → 0/2176 |
| 16 / ZH | 155.952 → 155.101 | 102.09 → 102.53 | 139.50/137.40 → 138.29/139.42 | 57.90/58.70 → 59.40/60.00 | 79.40/79.50 → 80.50/81.60 | 0.5874/0.5933 → 0.5874/0.5993 | 0/4040 → 0/4040 |
