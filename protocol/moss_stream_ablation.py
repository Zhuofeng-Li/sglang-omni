"""Isolate async decode on the frozen MOSS candidate; never rewrite primary data."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import traceback

import yaml

ROOT = Path(os.environ.get("QUAL_ROOT", "/qualification"))
SOURCE = ROOT / "source/pr-2859"
ORDER = [("default", 42), ("async-off", 42), ("async-off", 43), ("default", 43)]
GPU = "GPU-e9f60c1d-8856-043c-42cd-47a942a4d8f1"


def save(path, value):
    temporary = path.with_suffix(".partial")
    temporary.write_text(json.dumps(value, indent=2))
    temporary.replace(path)


def config(variant):
    return {
        "config_cls": "MossTTSPipelineConfig",
        "model_path": str(ROOT / "assets/moss"),
        "stages": {
            "preprocessing": {"factory": {"codec_model_path": str(ROOT / "assets/codec")}},
            "tts_engine": {"gpu_memory_fraction": 0.60, "factory": {"enable_async_decode": variant == "default"}},
            "vocoder": {"factory": {"codec_model_path": str(ROOT / "assets/codec")}},
        },
    }


def cases():
    return [{"name": f"pr2859-ablation-c64-stream-{variant}-seed{seed}", "variant": variant, "seed": seed, "config": config(variant)} for variant, seed in ORDER]


def digest_source(protocol):
    digest = hashlib.sha256()
    for name in protocol["source_files"]:
        digest.update(name.encode() + b"\0" + (SOURCE / name).read_bytes())
    return digest.hexdigest()


def scorer_files(identity):
    rows = []
    for row in identity["files"]:
        path = Path(identity["cache"]) / row["name"]
        with path.open("rb") as stream:
            digest = hashlib.file_digest(stream, "sha256").hexdigest()
        assert digest == row["sha256"]
        rows.append({"name": row["name"], "sha256": digest, "size_bytes": path.stat().st_size})
    return rows


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--describe", action="store_true")
    args = parser.parse_args()
    if args.describe:
        print(json.dumps(cases(), indent=2))
        return
    protocol_path = ROOT / "control/moss-ablation-protocol.json"
    protocol = json.loads(protocol_path.read_text())
    protocol_sha = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
    assert protocol["cases"] == cases()
    assert hashlib.sha256((ROOT / "control/pinned_tts_benchmark.py").read_bytes()).hexdigest() == protocol["benchmark_sha256"]
    assert json.loads((ROOT / "control/moss-quality-state.json").read_text())["status"] == "complete", "Primary quality must finish before any ablation GPU work"
    identity = json.loads((ROOT / "control/moss-scorer-identity.json").read_text())
    assert identity["verified_unchanged_after_all_scores"]
    assert digest_source(protocol) == protocol["source_digest_sha256"]
    scorer_before = scorer_files(identity)
    state_path = ROOT / "control/moss-ablation-state.json"
    if state_path.exists() and json.loads(state_path.read_text())["status"] == "complete":
        verified = json.loads((ROOT / "control/moss-ablation-verification.json").read_text())
        assert verified["protocol_sha256"] == protocol_sha
        assert verified["scorer_files"] == scorer_before and verified["verified_scorers_unchanged"]
        return
    state = {"status": "starting", "cases": [], "protocol_sha256": protocol_sha, "controller_pid": os.getpid()}

    def progress(status, **fields):
        state.update(status=status, at=time.time(), **fields)
        save(state_path, state)

    try:
        for index, case in enumerate(cases()):
            directory = ROOT / "moss-ablation-results" / case["name"]
            directory.mkdir(parents=True, exist_ok=True)
            result_path = directory / "result.json"
            if result_path.exists():
                result = json.loads(result_path.read_text())
                assert result["protocol_sha256"] == protocol_sha and result["exit_code"] == 0, "Inspect an existing failed/incompatible attempt instead of overwriting it"
                state["cases"].append(case["name"])
                continue
            assert not (directory / "operator.log").exists(), "Inspect and preserve an unfinished attempt before retrying it"
            (directory / "config.yaml").write_text(yaml.safe_dump(case["config"]))
            env = dict(os.environ, PYTHONPATH=str(ROOT / "control/telemetry") + ":" + str(SOURCE), PYTHONHASHSEED=str(case["seed"]), OMP_NUM_THREADS="8", MKL_NUM_THREADS="8", QUAL_GRAPH_DIR=str(directory / "graphs"), TOKENIZERS_PARALLELISM="false", SGLANG_ENABLE_JIT_DEEPGEMM="0", SEEDTTS_SIM_CACHE_DIR=str(ROOT / "cache/sim"))
            for name in ["TORCHINDUCTOR_CACHE_DIR", "TRITON_CACHE_DIR", "CUDA_CACHE_PATH", "TORCH_EXTENSIONS_DIR", "SGLANG_JIT_CACHE_DIR", "FLASHINFER_WORKSPACE_BASE"]:
                env[name] = str(ROOT / "moss-compile" / case["name"] / name)
                Path(env[name]).mkdir(parents=True, exist_ok=True)
            command = [sys.executable, str(ROOT / "control/pinned_tts_benchmark.py"), "--generate-only", "--port", str(20500 + index), "--model", str(ROOT / "assets/moss"), "--server-config", str(directory / "config.yaml"), "--meta", "zhaochenyang20/seed-tts-eval-arrow", "--ref-format", "references", "--token-count", "auto", "--concurrency", "64", "--warmup", "16", "--seed", str(case["seed"]), "--max-new-tokens", "2048", "--server-timeout", "1200", "--skip-gpu-cleanup", "--output-dir", str(directory), "--stream"]
            actual_gpu = subprocess.check_output(["nvidia-smi", "--query-gpu=uuid", "--format=csv,noheader"], text=True).strip()
            assert actual_gpu == GPU and digest_source(protocol) == protocol["source_digest_sha256"]
            started = time.time()
            peak = 0
            with (directory / "operator.log").open("w") as output:
                child = subprocess.Popen(command, cwd=SOURCE, env=env, stdout=output, stderr=subprocess.STDOUT, start_new_session=True)
                while child.poll() is None:
                    memory = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True)
                    if memory.returncode == 0:
                        peak = max(peak, int(memory.stdout.strip()))
                    progress("generating", current=case["name"], pid=child.pid, elapsed_s=time.time() - started)
                    if time.time() - started > 10800:
                        os.killpg(child.pid, signal.SIGTERM)
                        child.wait(timeout=30)
                        raise TimeoutError(case["name"])
                    time.sleep(0.5)
            result = dict(case, source=str(SOURCE), candidate=protocol["candidate"], source_digest_sha256=protocol["source_digest_sha256"], protocol_sha256=protocol_sha, gpu_uuid=actual_gpu, command=command, started_at=started, finished_at=time.time(), peak_mib=peak, exit_code=child.returncode)
            save(result_path, result)
            assert child.returncode == 0, case["name"]
            state["cases"].append(case["name"])
        # Score every new generation with the already verified primary scorers.
        sys.path.insert(0, str(ROOT / "source/main"))
        from benchmarks.benchmarker.utils import managed_omni_server
        os.chdir(ROOT / "source/main")
        command = [sys.executable, str(ROOT / "control/pinned_tts_benchmark.py"), "--meta", "zhaochenyang20/seed-tts-eval-arrow", "--model", str(ROOT / "assets/moss"), "--asr-model-path", str(ROOT / "assets/model"), "--asr-concurrency", "32", "--lang", "en", "--device", "cuda:0"]
        os.environ["SEEDTTS_SIM_CACHE_DIR"] = str(ROOT / "cache/sim")
        with managed_omni_server(model_path=str(ROOT / "assets/model"), port=19000, host="127.0.0.1", log_file=ROOT / "control/moss-ablation-asr-server.log", timeout=1200, wait_for_gpu_release=False):
            for case in cases():
                directory = ROOT / "moss-ablation-results" / case["name"]
                progress("transcribing", current=case["name"])
                if not (directory / "wer_results.json").exists():
                    with (directory / "wer.log").open("w") as output:
                        subprocess.run(command + ["--transcribe-only", "--use-existing-server", "--host", "127.0.0.1", "--port", "19000", "--output-dir", str(directory)], check=True, stdout=output, stderr=subprocess.STDOUT)
        for case in cases():
            directory = ROOT / "moss-ablation-results" / case["name"]
            progress("scoring_similarity", current=case["name"])
            if not (directory / "similarity_results.json").exists():
                with (directory / "similarity.log").open("w") as output:
                    subprocess.run(command + ["--similarity-only", "--output-dir", str(directory)], check=True, stdout=output, stderr=subprocess.STDOUT)
        assert scorer_files(identity) == scorer_before
        assert digest_source(protocol) == protocol["source_digest_sha256"]
        intervals = []
        for case in cases():
            directory = ROOT / "moss-ablation-results" / case["name"]
            result = json.loads((directory / "result.json").read_text())
            intervals.append((result["started_at"], result["finished_at"]))
            for kind in ["speed", "wer", "similarity"]:
                measured = json.loads((directory / f"{kind}_results.json").read_text())
                assert len(measured.get("per_request", measured.get("per_sample", []))) == 1088
                summary = measured["summary"]
                if kind == "speed":
                    assert summary["completed_requests"] == summary["total_requests"] == 1088 and summary["failed_requests"] == 0
                else:
                    assert summary["evaluated"] == summary["total_samples"] == 1088 and summary["skipped"] == 0
                    assert math.isfinite(summary["wer_corpus" if kind == "wer" else "speaker_similarity_mean"])
        assert all(intervals[index][1] < intervals[index + 1][0] for index in range(3))
        save(ROOT / "control/moss-ablation-verification.json", {"protocol_sha256": protocol_sha, "source_digest_sha256": protocol["source_digest_sha256"], "scorer_files": scorer_before, "verified_scorers_unchanged": True, "validated_cases": 4, "completed_at": time.time()})
        progress("complete")
    except Exception as error:
        progress("failed", error=repr(error), traceback=traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
