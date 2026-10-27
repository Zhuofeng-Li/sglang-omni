# Ming series integration with main

This is a local cumulative compatibility check, not independent PR performance or CI on a published revision.

- Published series head: `8d0f5d4352b704986cbc50e44ec4df42cce0fbc9`.
- Main integration base: `e9c058462d104451aa5144b12b001b0709a94a55`.
- Uncommitted merge tree: `4c02de011867bef32cbec1b93f0929a219947fec`; merge was conflict-free.
- Complete diff against main: 38 files; only the explicitly requested `docs/cookbook/ming3_tts.md` under doc/docs.
- CPU test result: **606 passed, 42 skipped, 2 failed**. All collected Ming-family tests passed. The two failures are the parameterized shared stream-priority test: the CPU Torch build has no `torch.cuda.Stream.priority_range`, so monkeypatch setup fails before the implementation runs. Both shared source and test files are unchanged from this main base. No assertions were relaxed or tests deselected.
- Environment: CPU Torch2.14.1, torchaudio2.11.0, torchvision0.29.1, Transformers5.19.0, SGLang0.5.22. Commands and exact source IDs are in the accompanying JSON.
- Initial setup attempts exposed absent Python dependencies and an old CPU Torch environment; these were corrected in isolated dependency directories without changing the measured GPU image or model source.

Full CUDA integration and the final merged-series performance comparison remain required.
