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

## Ming3 quality repeat

[Machine-readable hashes](quality-audio-index.json).

| Cell / seed / sample | Control | PR | Historical waveform hash match (A/B) |
|---|---|---|---|
| quality-en-c16 / 42<br>common_voice_en_18057869-common_voice_en_18057867 | [WAV](quality/quality-results/quality-en-c16-A42/output/audio/common_voice_en_18057869-common_voice_en_18057867.wav)<br>Wrapped in a scarf and blinded by the blizzard, the boy scrambled for the subway.<br>0 ASR edits | [WAV](quality/quality-results/quality-en-c16-B42/output/audio/common_voice_en_18057869-common_voice_en_18057867.wav)<br>Wrapped in a scarf and blinded by the blizzard, the boys scrambled for the subway.<br>1 ASR edits | yes/no |
| quality-en-c16 / 42<br>common_voice_en_25568854-common_voice_en_25568851 | [WAV](quality/quality-results/quality-en-c16-A42/output/audio/common_voice_en_25568854-common_voice_en_25568851.wav)<br>To communicate over the longest distances, Hams use moon bounce.<br>0 ASR edits | [WAV](quality/quality-results/quality-en-c16-B42/output/audio/common_voice_en_25568854-common_voice_en_25568851.wav)<br>To communicate over the longest distances, Hams use moon bounce.<br>0 ASR edits | yes/no |
| quality-en-c16 / 43<br>common_voice_en_19211875-common_voice_en_19211870 | [WAV](quality/quality-results/quality-en-c16-A43/output/audio/common_voice_en_19211875-common_voice_en_19211870.wav)<br>The airport is served by Calm Air and Perimeter Aviation with flights to Winnipeg.<br>0 ASR edits | [WAV](quality/quality-results/quality-en-c16-B43/output/audio/common_voice_en_19211875-common_voice_en_19211870.wav)<br>The airport is served by Comair and Perimeter Aviation with flights to Winnipeg.<br>2 ASR edits | yes/no |
| quality-zh-c1 / 42<br>00004504-00000057 | [WAV](quality/quality-results/quality-zh-c1-A42/output/audio/00004504-00000057.wav)<br>尽管是用民间资金办学，但亚奥学校的性质并不单纯。<br>0 ASR edits | [WAV](quality/quality-results/quality-zh-c1-B42/output/audio/00004504-00000057.wav)<br>尽管是用民间资金办学，但雅澳学校的性质并不单纯。<br>2 ASR edits | yes/yes |
| quality-zh-c1 / 42<br>00013652-00000048 | [WAV](quality/quality-results/quality-zh-c1-A42/output/audio/00013652-00000048.wav)<br>产品经理其实是随着互联网发展应运而生的。<br>0 ASR edits | [WAV](quality/quality-results/quality-zh-c1-B42/output/audio/00013652-00000048.wav)<br>成为经理其实是随着互联网发展应运而生的。<br>2 ASR edits | yes/yes |
| quality-zh-c1 / 43<br>00004895-00000090 | [WAV](quality/quality-results/quality-zh-c1-A43/output/audio/00004895-00000090.wav)<br>致使银行的同业业务和表外业务出现了明显收缩。<br>0 ASR edits | [WAV](quality/quality-results/quality-zh-c1-B43/output/audio/00004895-00000090.wav)<br>这是银行的同业业务和表外业务出现了明显收缩。<br>2 ASR edits | yes/yes |
| quality-zh-c1 / 43<br>00005257-00000065 | [WAV](quality/quality-results/quality-zh-c1-A43/output/audio/00005257-00000065.wav)<br>办公和电信设备的出口占比在二零零九年超越欧盟以后，稳居第一。<br>0 ASR edits | [WAV](quality/quality-results/quality-zh-c1-B43/output/audio/00005257-00000065.wav)<br>办公和电信设备的出口占比在2009年超越欧盟以后，稳居第一。<br>4 ASR edits | yes/yes |

