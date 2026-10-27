"""Verify main's ASR-loader wrapper preserves pinned-image WAV preparation."""
from pathlib import Path
import hashlib
import json

import torch
import torchaudio

from benchmarks.tasks.asr import _load_wav_mono_16k, _wav_bytes_from_mono_16k
from sglang_omni.utils.audio import check_torchcodec_ready, load_with_torchaudio

torch.set_num_threads(1)
root = Path('/results')
assert check_torchcodec_ready(), 'The comparison must exercise the pinned preferred decoder path'
paths = sorted((root / 'output/audio').glob('*.wav'))
assert len(paths) >= 8
rows = []
for path in paths[:4] + paths[-4:]:
    old = _load_wav_mono_16k(str(path))
    audio, rate = load_with_torchaudio(str(path), source_name='ASR benchmark')
    if audio.ndim == 2 and audio.shape[0] > 1:
        audio = audio.mean(dim=0, keepdim=True)
    new = audio.squeeze(0).to(torch.float32)
    if rate != 16000:
        new = torchaudio.functional.resample(new, rate, 16000)
    assert torch.equal(old, new), path.name
    old_bytes, new_bytes = _wav_bytes_from_mono_16k(old), _wav_bytes_from_mono_16k(new)
    assert old_bytes == new_bytes
    rows.append({'id': path.stem, 'samples_16k': len(old),
                 'pcm16_wav_sha256': hashlib.sha256(old_bytes).hexdigest()})
assert not torch.cuda.is_initialized(), 'The decoder probe must remain CPU-only'
result = {'main_change': '71bce692cea4a5b694e1f6de69900181d5abc138',
          'torch': torch.__version__, 'torchaudio': torchaudio.__version__,
          'torchcodec_ready': True, 'cuda_initialized': False,
          'equal_tensor_and_pcm16_bytes': True, 'cases': rows}
(root / 'main71-decoder-equivalence.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result))
