# Ming3 streaming review evidence

Measurement is in progress. Partial results below do not establish complete latency or quality qualification.

Frozen integration commit: `251f02b467fe06269cb2d3d8c1063565d7c3de82`; final dense branch has the identical Git tree. One H200; first 128 SeedTTS EN and ZH samples, two seeds, c1/c32, mode order nonstream42 / stream42 / stream43 / nonstream43. First audio is measured from request dispatch to first nonempty PCM. Playback starts on arrival; fewer than two chunks is N/A for underrun. See source-identity.json, operator scripts, raw per-request records and summary.json.

PRs: [3189](https://github.com/sgl-project/sglang-omni/pull/3189), [3190](https://github.com/sgl-project/sglang-omni/pull/3190). Non-streaming prerequisite: [3136](https://github.com/sgl-project/sglang-omni/pull/3136).
