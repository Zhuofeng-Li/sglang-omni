"""Score every requested paired Delay cohort before discarding generated audio."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path("/qualification")
sys.path.insert(0, str(ROOT / "source/main"))
from benchmarks.benchmarker.utils import managed_omni_server

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
    progress.update(status="complete")
    save()
except Exception as error:
    progress.update(status="failed", error=repr(error))
    save()
    raise
