# Tiny full-graph and streaming-cache integration

Source `8d0f5d4352b704986cbc50e44ec4df42cce0fbc9`, combining the Tiny precision/full-vocoder graphs with the existing Tiny/dense streaming stack. One H100 80GB, assigned GPU `GPU-7cea2752-34c7-f9c2-cd45-79163c61c398`; image `afb9f5ee0a17c70fe47598fa4802c6f1926bdd39c23fe1d35c8b14f701da0c23`. PyTorch 2.14.1, SGLang 0.5.22, Transformers 5.19.0. This is functional validation, not a paired performance experiment.

- Full targeted Ming3/Ming-TTS/MPS/CPU-locality/scheduler/stage-environment suite: **428 passed, 6 skipped** (141.62s). The Tiny and dense variants of the full-graph versus incremental-cache routing regression both ran on CUDA. The six skips are unsupported native-normalization tiles with eager fallback.
- Real Tiny checkpoint `7bd9446a8d47e462362261a0150258da6d458318`: **14 PCM cases passed**, plus SSE terminal usage/finish-reason checks, four concurrent streams, disconnect recovery and a one-latent terminal flush.
- **250 complete exact-length vocoder graphs captured** from `vocoder_graph.py`. The unit routing assertions verify full graph dispatch for non-streaming, with no full-decode call for subsequent streaming chunks.
- All four EN/ZH × reference/no-reference full/stream pairs produced matching sample counts and normalized ASR transcripts. WER/CER here is a small functional check, not full-corpus qualification.
- Host cleanup verified no GPU clients, no running containers, and both test ports released. The H100 assignment was released after the final off-node archive was verified.

The smoke command uses mem-fraction-static0.6, max-running/graph-batch32, seed42 and a250-token cap; it preserves the registered Tiny GPU preprocessing/async/MPS defaults and full250-length vocoder capture. The source scripts and exact commands are retained below.

The first asset-download attempt inherited the image's offline setting and failed before downloading. The corrected download-only environment sets the offline variables to0; the completed unit suite was retained. All65 downloaded files were checked against the pinned revision and their Hub Git/LFS hashes. No model weights or raw audio are copied here; the output hashes, sample counts, transcripts and source/version manifests are retained.

This functional result does not establish independent Tiny performance benefits. Tiny acoustic/preprocessing changes affect streaming as well as non-streaming; both modes need current-main paired performance/quality/cost qualification. [Earlier Tiny bundle evidence](https://github.com/Zhuofeng-Li/sglang-omni/blob/codex/ming3-tiny-c24-evidence/evidence/ming3-tiny-c24/report.md) retains its original source revisions and is not an independent result for this head.

## Publication and dependency order

The original four PRs are now linked in native [stack #3254](https://github.com/sgl-project/sglang-omni/stack/3254): #3136 → #3189 → #3190 → #3217. All heads and draft states were preserved while the stack metadata was aligned. #3217 is still Draft, with current-main performance validation pending for both modes. The [new exact-head manual CI](https://github.com/sgl-project/sglang-omni/actions/runs/40466048020) verified unit-only preflight at `8d0f5d4`. CPU A passed 4,733 tests (87 skipped), CPU B passed 5,308 (36 skipped), and accelerator passed 1,145 (34 skipped), including both graph/cache routing cases. Workflow environment cleanup is queued; see `ci-current.json`.
