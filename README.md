# PR review fixes and qualification

Evidence for sgl-project/sglang-omni #2880, #2881, #2882 and the requested #2859 concurrency backfill. This branch is separate from every upstream PR patch. Archived descriptions retain historical results, measurement dates and source identities. Final-source paired performance qualification is pending; correctness results are recorded per PR.

Frozen control: 2d5de98cd92b17df7974ac2ef4192b4a99263845. One Radix H100 80GB, seeds 42/43, same-card ABBA blocks, two modes. Qwen uses full EN/ZH and c1/c16/c32/c64. MOSS backfills the requested EN c1/c64. Quality, failures and startup/memory/graph costs are retained. No old-head result is relabeled as a new-head measurement.

Separately labeled review work at c32 includes FlashInfer FULL coverage against an eager-prefill reference, FULL/exact-bucket glue on/off, async-prefill with original versus scoped admission, repeated seed-42/order blocks for all three Qwen PRs, and saved normalized transcript differences. Those are component/backend/repetition evidence, not clean-main standalone improvement claims.
