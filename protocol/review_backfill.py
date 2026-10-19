"""Run separately labeled review ablations, backend coverage and fixed-seed repeats."""
import ast
import difflib
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from run_pair import cohort

ROOT = Path(os.environ["QUAL_ROOT"])
state = {"status": "preparing", "cases": []}


def save():
    state["at"] = time.time()
    temporary = ROOT / "control/review-backfill-state.partial"
    temporary.write_text(json.dumps(state, indent=2))
    temporary.replace(ROOT / "control/review-backfill-state.json")


def run(pr, arm, seed, mode, label, *, source=None, engine=None, environment=None, smoke=False):
    state.update(status="running", current=f"{label}/{pr}/{arm}/{seed}/{mode}")
    save()
    result = cohort(pr, arm, seed, mode, 32, smoke=smoke, tag=label, source_name=source, engine_overrides=engine, env_overrides=environment)
    expected = {"en": 8, "zh": 8} if smoke else {"en": 1088, "zh": 2020}
    assert result["status"] == "completed"
    for language, count in expected.items():
        summary = result["measurements"][language]["summary"]
        assert summary["evaluated"] == count and summary["skipped"] == 0
    record = {"name": result["name"], "pr": pr, "arm": arm, "seed": seed, "mode": mode, "label": label, "smoke": smoke, "source": source or ("main" if arm == "main" else f"pr-{pr}"), "engine_overrides": engine or {}, "environment_overrides": environment or {}}
    if label.startswith("flashinfer") and arm == "full":
        graph_counts = result["graphs_after_scoring"]["callers"]
        captures = sum(count for caller, count in graph_counts.items() if "prefill_cuda_graph_runner.py" in caller)
        assert captures > 0, "FULL prefill did not capture with FlashInfer; do not claim backend coverage"
        log = (ROOT / "results" / result["name"] / "server.log").read_text()
        evidence = re.findall(r".{0,100}(?:attention_backend=['\"]?flashinfer|[Ff]lash[Ii]nfer.{0,50}attention|attention.{0,50}[Ff]lash[Ii]nfer).{0,100}", log)
        assert evidence, "No FlashInfer backend evidence in startup log"
        record.update(full_prefill_successful_captures=captures, backend_log_evidence=evidence[:8])
    state["cases"].append(record)
    save()


try:
    scheduler = Path("sglang_omni/scheduling/omni_scheduler.py")
    original = (ROOT / "source/main" / scheduler).read_text()
    final = (ROOT / "source/pr-2881" / scheduler).read_text()
    methods = ["process_input_requests", "drain_request_build_results", "get_new_batch_prefill"]
    main_class = next(node for node in ast.parse(original).body if isinstance(node, ast.ClassDef) and node.name == "OmniScheduler")
    final_class = next(node for node in ast.parse(final).body if isinstance(node, ast.ClassDef) and node.name == "OmniScheduler")
    original_lines = original.splitlines(keepends=True)
    final_lines = final.splitlines(keepends=True)
    replacements = []
    for name in methods:
        left = next(node for node in main_class.body if isinstance(node, ast.FunctionDef) and node.name == name)
        right = next(node for node in final_class.body if isinstance(node, ast.FunctionDef) and node.name == name)
        replacements.append((right.lineno - 1, right.end_lineno, original_lines[left.lineno - 1:left.end_lineno]))
    for start, end, replacement in sorted(replacements, reverse=True):
        final_lines[start:end] = replacement
    ablation = "".join(final_lines)
    ast.parse(ablation)
    destination = ROOT / "source/pr-2881-async-only"
    if not destination.exists():
        shutil.copytree(ROOT / "source/pr-2881", destination)
    (destination / scheduler).write_text(ablation)
    patch = "".join(difflib.unified_diff(final.splitlines(keepends=True), ablation.splitlines(keepends=True), fromfile="a/" + str(scheduler), tofile="b/" + str(scheduler)))
    (ROOT / "control/async-only-variant.patch").write_text(patch)
    state["async_only_variant"] = {"methods_restored_from_frozen_main": methods, "patch_sha256": hashlib.sha256(patch.encode()).hexdigest(), "scope": "Async prefill retained; original FIFO/input-wait admission restored. Both arms retain upstream MRoPE positions."}
    save()

    for smoke in [True, False]:
        for mode in ["nonstream", "stream"]:
            order = [("eager", 42), ("full", 42)] if smoke else [("eager", 42), ("full", 42), ("full", 43), ("eager", 43)]
            for arm, seed in order:
                engine = {"attention_backend": "flashinfer"}
                if arm == "eager":
                    engine["cuda_graph_backend_prefill"] = "disabled"
                run(2880, arm, seed, mode, "flashinfer-full-coverage", source="main" if arm == "eager" else "pr-2880", engine=engine, environment={"SGLANG_ENABLE_METADATA_GLUE_GRAPH": "0"}, smoke=smoke)

    for mode in ["nonstream", "stream"]:
        for arm, seed in [("no_glue", 42), ("glue", 42), ("glue", 43), ("no_glue", 43)]:
            run(2880, arm, seed, mode, "full-exact-buckets-glue-ablation", source="pr-2880", environment={"SGLANG_ENABLE_METADATA_GLUE_GRAPH": "1" if arm == "glue" else "0"})
        for arm, seed in [("async_only", 42), ("scoped_admission", 42), ("scoped_admission", 43), ("async_only", 43)]:
            run(2881, arm, seed, mode, "async-admission-ablation", source="pr-2881-async-only" if arm == "async_only" else "pr-2881")

    for pr in [2880, 2881, 2882]:
        for mode in ["nonstream", "stream"]:
            for arm, repetition in [("main", 1), ("pr", 1), ("pr", 2), ("main", 2)]:
                run(pr, arm, 42, mode, f"fixed-seed42-repeat{repetition}")

    state.update(status="complete", expected_cases=52)
    assert len(state["cases"]) == 52
    save()
    subprocess.run([sys.executable, str(ROOT / "control/quality_differences.py")], check=True)
except Exception as error:
    state.update(status="failed", error=repr(error))
    save()
    raise
