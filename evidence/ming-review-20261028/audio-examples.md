# Selected paired audio examples

The CSV field `whisper_text` below is Qwen3-ASR output. The WAV links and hash indexes preserve measured files; ASR spelling differences are not automatically audio-quality regressions. These examples include both worse and better scores. Full paired metrics/transcript differences remain in the main report.

## Ming-Omni shared-model check

[Machine-readable hashes](omni-audio-index.json).

| Cell / seed / sample | Control | PR | Historical waveform hash match (A/B) |
|---|---|---|---|
| omni-en-c8-full / 43<br>common_voice_en_15265-common_voice_en_15266 | [WAV](omni/omni-results/omni-en-c8-full-A43/output/audio/common_voice_en_15265-common_voice_en_15266.wav)<br>Large brown dog walks up a blue staircase.<br>0 ASR edits | [WAV](omni/omni-results/omni-en-c8-full-B43/output/audio/common_voice_en_15265-common_voice_en_15266.wav)<br>A large brown dog walks up a blue staircase.<br>1 ASR edits | N/A (new shared-model check) |
| omni-en-c8-stream / 42<br>common_voice_en_15734837-common_voice_en_15734838 | [WAV](omni/omni-results/omni-en-c8-stream-A42/output/audio/common_voice_en_15734837-common_voice_en_15734838.wav)<br>Tyler, Lucy, Michelle, we're going to space.<br>0 ASR edits | [WAV](omni/omni-results/omni-en-c8-stream-B42/output/audio/common_voice_en_15734837-common_voice_en_15734838.wav)<br>Tyler, Lucy, Michelle were going to space.<br>2 ASR edits | N/A (new shared-model check) |
| omni-zh-c1-stream / 43<br>10002698-00000106 | [WAV](omni/omni-results/omni-zh-c1-stream-A43/output/audio/10002698-00000106.wav)<br>此外，还有毒蛇、蟒蛇经常出现，给发展生造成许多困难。<br>0 ASR edits | [WAV](omni/omni-results/omni-zh-c1-stream-B43/output/audio/10002698-00000106.wav)<br>此外，还有毒蛇、蟒蛇经常出现，给发展商造成许多困难。<br>1 ASR edits | N/A (new shared-model check) |
| omni-zh-c8-full / 43<br>10002508-00000062 | [WAV](omni/omni-results/omni-zh-c8-full-A43/output/audio/10002508-00000062.wav)<br>十班警长陈真和同事立即赶往事发地工商银行。<br>1 ASR edits | [WAV](omni/omni-results/omni-zh-c8-full-B43/output/audio/10002508-00000062.wav)<br>值班警长陈真和同事立即赶往事发地工商银行。<br>0 ASR edits | N/A (new shared-model check) |
| omni-zh-c8-stream / 42<br>10002290-00000102 | [WAV](omni/omni-results/omni-zh-c8-stream-A42/output/audio/10002290-00000102.wav)<br>说说你们在京藏高速怀安段堵车现场看到的情况。<br>0 ASR edits | [WAV](omni/omni-results/omni-zh-c8-stream-B42/output/audio/10002290-00000102.wav)<br>说说你们在京藏高速淮安段堵车现场看到的情况。<br>1 ASR edits | N/A (new shared-model check) |
| omni-zh-c8-stream / 43<br>10002290-00000102 | [WAV](omni/omni-results/omni-zh-c8-stream-A43/output/audio/10002290-00000102.wav)<br>说说你们在京藏高速淮安段堵车现场看到的情况。<br>1 ASR edits | [WAV](omni/omni-results/omni-zh-c8-stream-B43/output/audio/10002290-00000102.wav)<br>说说你们在京藏高速怀安段堵车现场看到的情况。<br>0 ASR edits | N/A (new shared-model check) |
| omni-zh-c8-stream / 43<br>10002539-00000018 | [WAV](omni/omni-results/omni-zh-c8-stream-A43/output/audio/10002539-00000018.wav)<br>打造更贴心、更细致的个性化服务。<br>0 ASR edits | [WAV](omni/omni-results/omni-zh-c8-stream-B43/output/audio/10002539-00000018.wav)<br>打打造更贴心、更细致的个性化服务。<br>1 ASR edits | N/A (new shared-model check) |
| omni-zh-c8-stream / 43<br>10002539-00000054 | [WAV](omni/omni-results/omni-zh-c8-stream-A43/output/audio/10002539-00000054.wav)<br>嗯。<br>16 ASR edits | [WAV](omni/omni-results/omni-zh-c8-stream-B43/output/audio/10002539-00000054.wav)<br>第一天去，前几个小时很尴尬，孤零零的。<br>0 ASR edits | N/A (new shared-model check) |

