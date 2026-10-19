"""Run isolated current-main ASR comparisons in balanced paired order."""
import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path
import random
import signal
import socket
import subprocess
import sys
import threading
import time

import requests
import yaml
from benchmarks.tasks import asr as asr_client
from benchmarks.dataset.seedtts import load_seedtts_samples
from benchmarks.eval.benchmark_asr_seedtts import run_asr_seedtts_once

ROOT = Path(os.environ["QUAL_ROOT"])
MODEL = str(ROOT / "assets/model")
DATASET = "zhaochenyang20/seed-tts-eval-arrow"
DATASET_REVISION = "27f4c1adee83b5b29b7c4b375f6b976324bda308"
PORT = 18880


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_text(json.dumps(value, indent=2))
    temporary.replace(path)


def memory_sample(stop, samples):
    while not stop.is_set():
        result = subprocess.run(["nvidia-smi", "--query-gpu=uuid,memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True)
        if result.returncode == 0:
            parts = result.stdout.strip().split(",")
            if len(parts) == 2:
                samples.append({"time": time.time(), "gpu": parts[0].strip(), "memory_mib": float(parts[1])})
        stop.wait(0.5)


def graph_totals(directory):
    captured = set()
    destroyed = set()
    callers = {}
    for path in directory.glob("graphs-*.jsonl"):
        for line in path.read_text().splitlines():
            row = json.loads(line)
            key = (row["pid"], row["token"])
            if row["event"] == "captured":
                captured.add(key)
                callers[row["caller"]] = callers.get(row["caller"], 0) + 1
            else:
                destroyed.add(key)
    return {"successful_captures": len(captured), "live_captures": len(captured - destroyed), "callers": callers}


async def strict_stream(response, result, start_time):
    deltas = []
    terminal = None
    seen_done = False
    last_delta = None
    async for raw_line in response.content:
        line = raw_line.decode("utf-8").strip()
        if not line.startswith("data: "):
            continue
        payload = line[6:]
        if payload == "[DONE]":
            seen_done = True
            continue
        event = json.loads(payload)
        kind = event.get("type")
        if kind == "error":
            raise ValueError("stream error event")
        if kind == "transcript.text.done":
            terminal = event.get("text")
        elif kind == "transcript.text.delta":
            delta = event.get("delta")
            if not isinstance(delta, str):
                raise ValueError("non-string text delta")
            if not delta:
                continue
            now = time.perf_counter()
            if result.text_ttft_s is None:
                result.text_ttft_s = now - start_time
            if last_delta is not None:
                result.inter_chunk_s.append(now - last_delta)
            last_delta = now
            deltas.append(delta)
    if not isinstance(terminal, str) or not seen_done:
        raise ValueError("incomplete terminal stream")
    if "".join(deltas) != terminal:
        raise ValueError("stream deltas differ from final text")
    return terminal.strip()


asr_client._consume_transcription_stream = strict_stream


def cohort(pr, arm, seed, mode, concurrency, smoke=False, *, tag=None, source_name=None, engine_overrides=None, env_overrides=None):
    name = f"pr{pr}-c{concurrency}-{mode}-{arm}-seed{seed}" + (f"-{tag}" if tag else "") + ("-smoke" if smoke else "")
    output = ROOT / "results" / name
    output.mkdir(parents=True, exist_ok=True)
    result_path = output / "result.json"
    if result_path.exists():
        return json.loads(result_path.read_text())
    source = ROOT / "source" / (source_name or ("main" if arm == "main" else f"pr-{pr}"))
    scratch = output / "scratch"
    scratch.mkdir(exist_ok=True)
    graph_dir = output / "graphs"
    config = {
        "config_cls": "Qwen3ASRPipelineConfig", "model_path": MODEL,
        "stages": {"asr": {"gpu": 0, "factory": {"dtype": "bfloat16", "pre_lm_cache_size_bytes": 1, "mm_embedding_cache_size_bytes": 0},
            "engine": {"disable_radix_cache": True, "random_seed": seed}}},
    }
    if engine_overrides:
        config["stages"]["asr"]["engine"].update(engine_overrides)
    config_path = output / "config.yaml"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False))
    env = dict(os.environ)
    env.update({"PYTHONPATH": str(ROOT / "control/telemetry") + ":" + str(source), "PYTHONHASHSEED": str(seed),
        "QUAL_GRAPH_DIR": str(graph_dir), "HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "TOKENIZERS_PARALLELISM": "false",
        "TORCHINDUCTOR_CACHE_DIR": str(scratch / "inductor"), "TRITON_CACHE_DIR": str(scratch / "triton"),
        "TORCH_EXTENSIONS_DIR": str(scratch / "extensions"), "CUDA_CACHE_PATH": str(scratch / "cuda"),
        "FLASHINFER_WORKSPACE_BASE": str(scratch / "flashinfer"), "TMPDIR": str(scratch)})
    if env_overrides:
        env.update(env_overrides)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as port_probe:
        port_probe.bind(("127.0.0.1", 0))
        port = port_probe.getsockname()[1]
    command = [sys.executable, "-m", "sglang_omni.cli", "serve", "--config", str(config_path), "--model-name", "Qwen/Qwen3-ASR-1.7B",
        "--host", "127.0.0.1", "--port", str(port), "--skip-server-warmup"]
    save(output / "launch.json", {"command": command, "source": str(source), "config": config, "seed": seed, "mode": mode, "concurrency": concurrency, "arm": arm, "environment_overrides": env_overrides or {}})
    samples_memory = []
    stop = threading.Event()
    monitor = threading.Thread(target=memory_sample, args=(stop, samples_memory), daemon=True)
    monitor.start()
    started = time.monotonic()
    server_log = (output / "server.log").open("w")
    process = subprocess.Popen(command, cwd=source, env=env, stdout=server_log, stderr=subprocess.STDOUT, start_new_session=True)
    result = {"pr": pr, "arm": arm, "seed": seed, "concurrency": concurrency, "mode": mode, "name": name, "status": "running", "measurements": {}}
    save(output / "status.json", result)
    try:
        session = requests.Session()
        session.trust_env = False
        while time.monotonic() - started < 900:
            if process.poll() is not None:
                raise RuntimeError(f"server exited before readiness: {process.returncode}")
            try:
                if session.get(f"http://127.0.0.1:{port}/health", timeout=2).status_code == 200:
                    break
            except requests.RequestException:
                pass
            time.sleep(0.5)
        else:
            raise TimeoutError("server readiness exceeded 900 seconds")
        result["startup_seconds"] = time.monotonic() - started
        result["graphs_at_ready"] = graph_totals(graph_dir)
        session.close()
        for language in ["en", "zh"]:
            samples = load_seedtts_samples(DATASET, max_samples=8 if smoke else None, split=language, revision=DATASET_REVISION)
            random.Random(seed).shuffle(samples)
            expected = 8 if smoke else {"en": 1088, "zh": 2020}[language]
            if len(samples) != expected:
                raise RuntimeError(f"wrong sample count: {language} {len(samples)}")
            fingerprint = hashlib.sha256("\n".join(sample.sample_id for sample in samples).encode()).hexdigest()
            stream = mode == "stream"
            warmup = asyncio.run(run_asr_seedtts_once(samples, "127.0.0.1", port, concurrency=min(concurrency, expected), lang=language, stream=stream))
            save(output / f"{language}-warmup-summary.json", {k: v for k, v in warmup.items() if k != "per_sample"})
            if warmup["summary"]["skipped"] or warmup["summary"]["evaluated"] != expected:
                raise RuntimeError(f"incomplete warmup for {language}")
            measured = asyncio.run(run_asr_seedtts_once(samples, "127.0.0.1", port, concurrency=min(concurrency, expected), lang=language, stream=stream))
            save(output / f"{language}-raw.json", measured)
            result["measurements"][language] = {k: v for k, v in measured.items() if k != "per_sample"}
            result["measurements"][language]["sample_order_sha256"] = fingerprint
            save(output / "status.json", result)
            if measured["summary"]["skipped"] or measured["summary"]["evaluated"] != expected:
                raise RuntimeError(f"incomplete scored pass for {language}")
        result["graphs_after_scoring"] = graph_totals(graph_dir)
        result["status"] = "completed"
    except Exception as error:
        result["status"] = "failed"
        result["error"] = repr(error)
        raise
    finally:
        stop.set()
        monitor.join(timeout=5)
        result["peak_memory_mib"] = max((r["memory_mib"] for r in samples_memory), default=None)
        save(output / "memory-samples.json", samples_memory)
        try:
            os.killpg(process.pid, signal.SIGTERM)
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.wait(timeout=20)
        except ProcessLookupError:
            pass
        server_log.close()
        save(output / "status.json", result)
        if result["status"] == "completed":
            save(result_path, result)
        print(json.dumps({"cohort": name, "status": result["status"], "error": result.get("error")}), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prs", nargs="+", type=int, default=[2880, 2881, 2882])
    parser.add_argument("--smoke", action="store_true")
    parser.add_argument("--concurrencies", nargs="+", type=int, default=[1,16,32,64])
    args = parser.parse_args()
    assert all(c in [1,16,32,64] for c in args.concurrencies)
    if not args.smoke and set(args.prs) == {2880, 2882}:
        # Check the requested alternative backend before the long primary
        # matrices. The final review hook reuses these same smoke results.
        subprocess.run([sys.executable, str(ROOT / "control/review_backfill.py"), "--backend-smoke-only"], check=True)
    if args.smoke:
        for arm in ["main", "pr"]:
            for mode in ["nonstream", "stream"]:
                cohort(args.prs[0], arm, 42, mode, 64, smoke=True)
    else:
        for pr in args.prs:
            for concurrency in args.concurrencies:
                for mode in ["nonstream", "stream"]:
                    for arm, seed in [("main", 42), ("pr", 42), ("pr", 43), ("main", 43)]:
                        cohort(pr, arm, seed, mode, concurrency)
    if not args.smoke and set(args.prs) == {2880, 2882}:
        subprocess.run([sys.executable, str(ROOT / "control/review_backfill.py")], check=True)
    save(ROOT / "results" / ("smoke-complete.json" if args.smoke else "complete-" + "-".join(map(str,args.prs)) + ".json"), {"prs": args.prs, "completed_at": time.time()})


if __name__ == "__main__":
    main()
