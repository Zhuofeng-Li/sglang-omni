# Ming series integration with main

This is a local cumulative compatibility check, not independent PR performance or CI on a published revision.

- Published series head: `8d0f5d4352b704986cbc50e44ec4df42cce0fbc9`.
- Main integration base: `e9c058462d104451aa5144b12b001b0709a94a55`.
- Uncommitted merge tree: `4c02de011867bef32cbec1b93f0929a219947fec`; merge was conflict-free.
- Complete diff against main: 38 files; only the explicitly requested `docs/cookbook/ming3_tts.md` under doc/docs.
- CPU test result: **606 passed, 42 skipped, 2 failed**. All collected Ming-family tests passed. The two failures are the parameterized shared stream-priority test: the CPU Torch build has no `torch.cuda.Stream.priority_range`, so monkeypatch setup fails before the implementation runs. Both shared source and test files are unchanged from this main base. No assertions were relaxed or tests deselected.
- Environment: CPU Torch2.14.1, torchaudio2.11.0, torchvision0.29.1, Transformers5.19.0, SGLang0.5.22. Commands and exact source IDs are in the accompanying JSON.
- Initial setup attempts exposed absent Python dependencies and an old CPU Torch environment; these were corrected in isolated dependency directories without changing the measured GPU image or model source.

## CUDA integration completed 2026-10-27

The same cumulative merge tree `4c02de011867bef32cbec1b93f0929a219947fec` completed **644 passed, 6 skipped, 0 failed** on the assigned H200. Both CPU-only stream-priority setup failures above pass under CUDA. No tests or assertions were relaxed.

Tiny and dense each passed 14 real HTTP PCM cases covering EN/ZH with/without reference audio, concurrent streaming, disconnect/recovery, and a one-latent terminal flush. SSE final packets include finish reason and usage. All eight matched offline/streaming pairs have identical sample counts and normalized ASR transcripts. Waveforms are not bit-identical: per-pair correlations are 0.9786–0.9998; raw comparisons and PCM hashes are retained in `current-main-cuda-audit.json` and the HTTP results. Tiny captured all 250 full vocoder graphs. These are functional smoke results, not a quality non-inferiority claim or a new performance comparison.

The test used image `afb9f5ee0a17c70fe47598fa4802c6f1926bdd39c23fe1d35c8b14f701da0c23` and GPU `GPU-4ac09667-48f7-6a03-b930-8338f78d441e`. Commands, preflight, source manifest, graph traces, and logs are under `cuda/`; audio is retained off-node and excluded from this public evidence snapshot. The full off-node archive SHA256 is `e2335148fb61b6a904bf9e6cefda5904c58d7aa649832429a9ca68586f824b52`.

After verification and backup, no containers or GPU clients remained; assignment `01M5XFE1DE8PVBQWTSDP2JDYRY` was released and confirmed absent. See `h200-release.json`.

## Linear stack provenance

The published linear stack is based on main `6087f786b3a9dd2d53dee5f321737cecda88dd12`. Each original PR remains separate and its cumulative tree exactly matches a clean merge of its original head with that main. The new top tree differs from the CUDA-tested tree only in `benchmarks/duplex/oracle.py` and `tests/unit_test/benchmarks/test_duplex_oracle.py`. This functional test does not substitute for CI on the published new heads. Original measured performance source IDs are unchanged. The final merged-series performance comparison and independent Tiny performance qualification remain required.

Public text logs normalize trailing whitespace; the off-node archive retains original bytes.

## Published-head CI

Manual [Omni CI 40588572290](https://github.com/sgl-project/sglang-omni/actions/runs/40588572290) succeeded on exact #3217 head `a818f498de01b9412283e13ed0fbf12cdb48a049`: CPU A 4,705 passed / 74 skipped; CPU B 5,601 / 49; accelerator 1,159 / 34. Both Tiny/dense full-graph versus incremental-cache routing tests passed. Preflight selected unit tests only, with all model stages disabled and no model preset. Final environment cleanup passed. This does not replace the pending independent Tiny performance comparison. Other PR CI results are recorded separately as they finish.
