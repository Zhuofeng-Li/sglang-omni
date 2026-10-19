### Original H100 review confirmation

<!-- pr2881-h100-review-confirmation-20261019 -->

Completed on **2026-10-19**, using the original H100 GPU, frozen main `2d5de98c` and final PR head `e98bcf05`: **24 measured cohorts**, full EN1088/ZH2020, zero failed/skipped samples. C32 admission ablation uses seeds42/43 ABBA (async prefill with frozen-main admission → final scoped admission). C32/C64 main→PR→PR→main repeats use fixed seed42 and identical order; these repeated executions are not independent random seeds. All original primary measurements remain unchanged.

| Comparison | Non-streaming EN/ZH geometric throughput change | Streaming EN/ZH geometric throughput change |
| --- | ---: | ---: |
| C32 admission only | +2.08% | +1.85% |
| C32 main → PR repeats | +9.87% | +9.68% |
| C64 main → PR repeats | +11.72% | +11.15% |

Per-repeat values below preserve the two executions separately (main → PR). Percentiles are per pass, not pooled; ASR SIM is N/A because there is no generated audio.

| Mode / C / language | req/s, repeats1/2 | Response p95 ms, repeats1/2 | First-text p95 ms, repeats1/2 | WER %, repeats1/2 |
| --- | --- | --- | --- | --- |
| nonstream / 32 / EN | 229.65/222.45 → 245.03/249.59 | 178.05/191.99 → 164.80/164.92 | N/A | 1.2258/1.2031 → 1.2107/1.2031 |
| nonstream / 32 / ZH | 239.89/244.19 → 269.81/264.27 | 174.23/171.13 → 154.91/161.55 | N/A | 0.5874/0.6053 → 0.6053/0.6083 |
| stream / 32 / EN | 218.91/222.42 → 247.77/237.86 | 184.51/183.02 → 165.40/168.63 | 98.20/98.60 → 101.40/101.20 | 1.2031/1.2107 → 1.2031/1.2031 |
| stream / 32 / ZH | 238.20/239.79 → 260.57/262.02 | 173.77/172.36 → 161.17/159.99 | 95.30/93.70 → 102.00/99.60 | 0.6143/0.6233 → 0.6143/0.6083 |
| nonstream / 64 / EN | 291.73/285.50 → 319.17/321.66 | 299.65/288.43 → 314.58/262.55 | N/A | 1.2107/1.2182 → 1.2107/1.2182 |
| nonstream / 64 / ZH | 304.87/307.64 → 343.02/345.65 | 283.26/272.57 → 247.98/253.05 | N/A | 0.5993/0.6293 → 0.6263/0.6173 |
| stream / 64 / EN | 276.03/281.62 → 299.61/310.20 | 306.85/298.41 → 279.19/310.56 | 181.90/179.80 → 179.90/234.70 | 1.2182/1.2182 → 1.2182/1.2258 |
| stream / 64 / ZH | 297.25/296.72 → 334.35/336.69 | 284.98/285.77 → 249.45/246.52 | 134.10/143.20 → 127.10/132.30 | 0.6173/0.6173 → 0.6233/0.6203 |

Across the 12 matched bilingual comparisons, 101 utterance comparisons change normalized text (33 improve per-utterance WER, 47 worsen, 21 equal); 28 distinct reference/left/right triples and 0 empty changed PR hypotheses. All28 distinct triples were inspected: changes involve names, homophones, singular/plural and short particles, sometimes reversing direction across comparisons. This does not establish equivalence, a numerical root cause or absence of truncation. C32 non-streaming ZH and C64 streaming ZH WER worsen in both fixed-seed repeats. The original extreme C64 EN first-text p95 of348.70ms is retained; these new repeats are181.90/179.80→179.90/234.70ms, so one improves and one worsens by54.90ms. Tail and quality tradeoffs still require independent review before readiness. Full per-pass measurements, costs, YAML, admission patch and changed transcripts are archived under `h100-review-confirmation-20261019` at the existing evidence link.
