"""Score every requested paired Delay cohort before discarding generated audio."""
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path("/qualification")
sys.path.insert(0, str(ROOT / "source/main"))
from benchmarks.benchmarker.utils import managed_omni_server
from benchmarks.metrics.speaker_similarity_assets import ensure_speaker_similarity_assets

folders = sorted(path for path in (ROOT / "moss-results").iterdir() if not path.name.endswith("-smoke"))
expected = {f"pr2859-c{concurrency}-{mode}-{arm}-seed{seed}" for concurrency in [1, 64] for mode in ["nonstream", "stream"] for arm, seed in [("main", 42), ("pr", 42), ("pr", 43), ("main", 43)]}
assert {path.name for path in folders} == expected
for path in folders:
    assert json.loads((path / "result.json").read_text())["exit_code"] == 0

progress = {"status": "starting", "completed": []}


def save():
    progress["at"] = time.time()
    temporary = ROOT / "control/moss-quality-state.partial"
    temporary.write_text(json.dumps(progress, indent=2))
    temporary.replace(ROOT / "control/moss-quality-state.json")


command = [sys.executable, str(ROOT / "control/pinned_tts_benchmark.py"), "--meta", "zhaochenyang20/seed-tts-eval-arrow", "--model", str(ROOT / "assets/moss"), "--asr-model-path", str(ROOT / "assets/model"), "--asr-concurrency", "32", "--lang", "en", "--device", "cuda:0"]
os.chdir(ROOT / "source/main")
try:
    # The serving image does not ship the SIM-only S3PRL dependency. Install
    # the verified pure-Python wheel only after timed generation has finished.
    wheel = ROOT / "assets/scorer-deps/s3prl-0.4.18-py3-none-any.whl"
    assert hashlib.sha256(wheel.read_bytes()).hexdigest() == "961225c224c1e6723788cdcb02e132c44d30871e60c897dfe9e3080e0ed505a4"
    try:
        scorer_version = importlib.metadata.version("s3prl")
    except importlib.metadata.PackageNotFoundError:
        subprocess.run([sys.executable, "-m", "pip", "install", "--no-deps", "--no-index", str(wheel)], check=True)
        scorer_version = importlib.metadata.version("s3prl")
    assert scorer_version == "0.4.18", scorer_version
    from s3prl.upstream.wavlm.hubconf import wavlm_local

    # Resolve once outside timed generation, then use exactly these cached
    # scorer weights for all arms. Save bytes/revisions without copying weights.
    os.environ["SEEDTTS_SIM_CACHE_DIR"] = str(ROOT / "cache/sim")
    progress.update(status="preparing_scorer_assets")
    save()
    assets = ensure_speaker_similarity_assets()
    scorer_paths = [assets.finetune_checkpoint, assets.wavlm_base]

    def scorer_identity():
        rows = []
        for path in scorer_paths:
            with path.open("rb") as stream:
                digest = hashlib.file_digest(stream, "sha256").hexdigest()
            metadata = path.parent / ".cache/huggingface/download" / (path.name + ".metadata")
            rows.append({"name": path.name, "size_bytes": path.stat().st_size, "sha256": digest, "hf_metadata": metadata.read_text().splitlines()[:3] if metadata.exists() else None})
        return rows

    initial_scorer_identity = scorer_identity()
    identity_path = ROOT / "control/moss-scorer-identity.json"
    identity = {"files": initial_scorer_identity, "s3prl_version": importlib.metadata.version("s3prl"), "cache": os.environ["SEEDTTS_SIM_CACHE_DIR"], "verified_unchanged_after_all_scores": False}
    identity_path.write_text(json.dumps(identity, indent=2))
    with managed_omni_server(model_path=str(ROOT / "assets/model"), port=19000, host="127.0.0.1", log_file=ROOT / "control/moss-asr-server.log", timeout=1200, wait_for_gpu_release=False):
        for path in folders:
            progress.update(status="transcribing", current=path.name)
            save()
            with (path / "wer.log").open("w") as output:
                subprocess.run(command + ["--transcribe-only", "--use-existing-server", "--host", "127.0.0.1", "--port", "19000", "--output-dir", str(path)], check=True, stdout=output, stderr=subprocess.STDOUT)
            progress["completed"].append([path.name, "WER"])
    for path in folders:
        progress.update(status="scoring_similarity", current=path.name)
        save()
        with (path / "similarity.log").open("w") as output:
            subprocess.run(command + ["--similarity-only", "--output-dir", str(path)], check=True, stdout=output, stderr=subprocess.STDOUT)
        progress["completed"].append([path.name, "SIM"])
    assert scorer_identity() == initial_scorer_identity, "Scorer weight identity changed during paired quality evaluation"
    identity["verified_unchanged_after_all_scores"] = True
    identity["verified_at"] = time.time()
    identity_path.write_text(json.dumps(identity, indent=2))
    progress.update(status="complete")
    save()
except Exception as error:
    progress.update(status="failed", error=repr(error))
    save()
    raise
