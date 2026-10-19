"""Reconcile final-source paired blocks without treating smoke as evidence."""
import datetime
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
heads = json.loads((ROOT / "heads.json").read_text())
audits = {}
for number in [2880, 2881, 2882]:
    rows = []
    for concurrency in [1, 16, 32, 64]:
        for mode in ["nonstream", "stream"]:
            for language, expected in [("en", 1088), ("zh", 2020)]:
                for arm, seed in [("main", 42), ("pr", 42), ("pr", 43), ("main", 43)]:
                    name = f"pr{number}-c{concurrency}-{mode}-{arm}-seed{seed}"
                    path = ROOT / "evidence/results" / name / "result.json"
                    row = dict(concurrency=concurrency, mode=mode, language=language, arm=arm, seed=seed, status="missing", evidence=str(path.relative_to(ROOT)))
                    if path.exists():
                        result = json.loads(path.read_text())
                        measurement = result.get("measurements", {}).get(language, {})
                        summary = measurement.get("summary", {})
                        if result.get("status") == "completed" and summary.get("evaluated") == expected and summary.get("skipped") == 0:
                            row.update(status="verified", sample_order_sha256=measurement.get("sample_order_sha256"), metrics=measurement)
                            row["costs"] = {key: result.get(key) for key in ["startup_seconds", "peak_memory_mib", "graphs_after_scoring"]}
                        else:
                            row.update(status="invalid", reason="Missing final completion or incomplete/full-split request counts")
                    rows.append(row)
    completed_cohort_cells = sum(row["status"] == "verified" for row in rows)
    blocks = []
    for concurrency in [1, 16, 32, 64]:
        for mode in ["nonstream", "stream"]:
            block_rows = [row for row in rows if row["concurrency"] == concurrency and row["mode"] == mode]
            block = dict(concurrency=concurrency, mode=mode, status="missing")
            if all(row["status"] == "verified" for row in block_rows):
                try:
                    intervals = []
                    launches = {}
                    for arm, seed in [("main", 42), ("pr", 42), ("pr", 43), ("main", 43)]:
                        directory = ROOT / "evidence/results" / f"pr{number}-c{concurrency}-{mode}-{arm}-seed{seed}"
                        memory = json.loads((directory / "memory-samples.json").read_text())
                        assert memory and {sample["gpu"] for sample in memory} == {"GPU-e9f60c1d-8856-043c-42cd-47a942a4d8f1"}
                        intervals.append((min(sample["time"] for sample in memory), max(sample["time"] for sample in memory)))
                        launch = json.loads((directory / "launch.json").read_text())
                        assert launch["source"] == f"/qualification/source/{'main' if arm == 'main' else f'pr-{number}'}"
                        assert launch["config"]["stages"]["asr"]["engine"]["random_seed"] == seed
                        launches[(arm, seed)] = launch["config"]
                    assert all(intervals[index][1] < intervals[index + 1][0] for index in range(3))
                    for seed in [42, 43]:
                        assert launches[("main", seed)] == launches[("pr", seed)]
                        for language in ["en", "zh"]:
                            matching = [row for row in block_rows if row["seed"] == seed and row["language"] == language]
                            assert len(matching) == 2 and matching[0]["sample_order_sha256"] == matching[1]["sample_order_sha256"]
                    block.update(status="verified", actual_abba_intervals=intervals)
                except (AssertionError, FileNotFoundError, KeyError) as error:
                    block.update(status="invalid", error=repr(error))
            if block["status"] != "verified":
                for row in block_rows:
                    if row["status"] == "verified":
                        row.update(status="missing" if block["status"] == "missing" else "invalid", reason="ABBA block is incomplete or failed pairing validation", individual_cohort_complete=True)
            blocks.append(block)
    audits[str(number)] = dict(frozen_main="2d5de98cd92b17df7974ac2ef4192b4a99263845", candidate=heads[str(number)], cells=rows, blocks=blocks, readiness="pending", completed_cohort_cells=completed_cohort_cells, covered=sum(row["status"] == "verified" for row in rows), expected=len(rows))
audits["2859"] = dict(frozen_main="2d5de98cd92b17df7974ac2ef4192b4a99263845", candidate=heads["2859"], scope="Requested c1/c64, EN full split, two modes, seeds 42/43 in ABBA order. Historical c16 retains its original source/date and is not final-main qualification.", readiness="pending", generations=[])
for concurrency in [1, 64]:
    for mode in ["nonstream", "stream"]:
        for arm, seed in [("main", 42), ("pr", 42), ("pr", 43), ("main", 43)]:
            name = f"pr2859-c{concurrency}-{mode}-{arm}-seed{seed}"
            directory = ROOT / "evidence/moss-results" / name
            row = dict(name=name, status="missing", quality="missing")
            if (directory / "result.json").exists():
                result = json.loads((directory / "result.json").read_text())
                row.update(status="generation_complete" if result.get("exit_code") == 0 else "invalid", result=result)
            if (directory / "wer-summary.json").exists() and (directory / "similarity-summary.json").exists():
                try:
                    speed = json.loads((directory / "speed-summary.json").read_text())
                    wer = json.loads((directory / "wer-summary.json").read_text())
                    similarity = json.loads((directory / "similarity-summary.json").read_text())
                    costs = json.loads((directory / "cost-summary.json").read_text())
                    assert speed["sample_count"] == speed["summary"]["total_requests"] == speed["summary"]["completed_requests"] == 1088
                    assert speed["summary"]["failed_requests"] == 0
                    for quality in [wer, similarity]:
                        assert quality["sample_count"] == quality["summary"]["total_samples"] == quality["summary"]["evaluated"] == 1088
                        assert quality["summary"]["skipped"] == 0
                    assert math.isfinite(wer["summary"]["wer_corpus"])
                    assert math.isfinite(similarity["summary"]["speaker_similarity_mean"])
                    assert costs["startup_seconds"] > 0
                    assert row["result"]["peak_mib"] > 0
                    assert row["result"]["gpu_uuid"] == "GPU-e9f60c1d-8856-043c-42cd-47a942a4d8f1"
                    row.update(status="measured", quality="verified", speed=speed, wer=wer, similarity=similarity, costs=costs)
                except (AssertionError, KeyError, FileNotFoundError) as error:
                    row.update(status="invalid", quality="invalid", error=repr(error))
            audits["2859"]["generations"].append(row)
audits["2859"]["blocks"] = []
for concurrency in [1, 64]:
    for mode in ["nonstream", "stream"]:
        names = [f"pr2859-c{concurrency}-{mode}-{arm}-seed{seed}" for arm, seed in [("main", 42), ("pr", 42), ("pr", 43), ("main", 43)]]
        rows = [next(row for row in audits["2859"]["generations"] if row["name"] == name) for name in names]
        block = dict(concurrency=concurrency, mode=mode, status="missing")
        if all(row["status"] == "measured" for row in rows):
            try:
                assert all(rows[index]["result"]["finished_at"] < rows[index + 1]["result"]["started_at"] for index in range(3))
                for left, right in [(rows[0], rows[1]), (rows[3], rows[2])]:
                    assert left["speed"]["sample_order_sha256"] == right["speed"]["sample_order_sha256"]
                    for key in ["seed", "concurrency", "max_new_tokens", "token_count", "warmup", "stream", "ref_format", "max_running_requests", "cuda_graph_max_bs"]:
                        assert left["speed"]["config"][key] == right["speed"]["config"][key]
                block.update(status="verified")
                for row in rows:
                    row["status"] = "verified"
            except (AssertionError, KeyError) as error:
                block.update(status="invalid", error=repr(error))
        audits["2859"]["blocks"].append(block)
review = {"status": "missing", "completed_cases": 0, "expected_cases": 52}
review_path = ROOT / "evidence/remote-control/review-backfill-state.json"
if review_path.exists():
    recorded = json.loads(review_path.read_text())
    review.update(status=recorded["status"], completed_cases=len(recorded["cases"]), groups=[])
    if recorded["status"] == "complete":
        try:
            assert len(recorded["cases"]) == 52
            groups = {}
            for case in recorded["cases"]:
                directory = ROOT / "evidence/results" / case["name"]
                result = json.loads((directory / "result.json").read_text())
                launch = json.loads((directory / "launch.json").read_text())
                memory = json.loads((directory / "memory-samples.json").read_text())
                assert result["status"] == "completed" and result["concurrency"] == 32
                assert launch["source"] == "/qualification/source/" + case["source"]
                assert launch["environment_overrides"] == case["environment_overrides"]
                for key, value in case["engine_overrides"].items():
                    assert launch["config"]["stages"]["asr"]["engine"][key] == value
                assert {sample["gpu"] for sample in memory} == {"GPU-e9f60c1d-8856-043c-42cd-47a942a4d8f1"}
                for language, count in [("en", 8 if case["smoke"] else 1088), ("zh", 8 if case["smoke"] else 2020)]:
                    summary = result["measurements"][language]["summary"]
                    assert summary["evaluated"] == count and summary["skipped"] == 0
                    assert math.isfinite(summary["wer_corpus"])
                if case["label"].startswith("flashinfer") and case["arm"] == "full":
                    assert case["full_prefill_successful_captures"] > 0 and case["backend_log_evidence"]
                    callers = result["graphs_after_scoring"]["callers"]
                    full_callers = {caller: count for caller, count in callers.items() if "prefill_cuda_graph_runner.py" in caller and "full_cuda_graph_backend.py:capture_one" in caller}
                    assert full_callers == case["full_prefill_capture_callers"]
                    assert sum(full_callers.values()) == case["full_prefill_successful_captures"]
                category = "fixed-seed42-repeat" if case["label"].startswith("fixed-seed42-repeat") else case["label"]
                key = (case["pr"], case["mode"], category, case["smoke"])
                groups.setdefault(key, []).append((case, result, (min(sample["time"] for sample in memory), max(sample["time"] for sample in memory))))
            assert len(groups) == 14
            for key, rows in groups.items():
                assert len(rows) == (2 if key[3] else 4)
                assert all(rows[index][2][1] < rows[index + 1][2][0] for index in range(len(rows) - 1))
                for left, right in ([rows[:2]] if key[3] else [rows[:2], rows[2:]]):
                    assert left[0]["seed"] == right[0]["seed"]
                    for language in ["en", "zh"]:
                        assert left[1]["measurements"][language]["sample_order_sha256"] == right[1]["measurements"][language]["sample_order_sha256"]
                review["groups"].append({"pr": key[0], "mode": key[1], "experiment": key[2], "smoke": key[3], "status": "verified", "cohorts": [row[0]["name"] for row in rows]})
            differences = json.loads((ROOT / "evidence/remote-control/quality-differences.json").read_text())
            assert len(differences["comparisons"]) == 120
            review["status"] = "verified"
        except (AssertionError, FileNotFoundError, KeyError) as error:
            review.update(status="invalid", error=repr(error))
payload = dict(observed_at_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), prs=audits, additional_review_validation=review)
(ROOT / "performance-audit.json").write_text(json.dumps(payload, indent=2))
print(json.dumps({number: {key: value.get(key) for key in ["covered", "expected", "readiness"]} for number, value in audits.items()}))

terminal_path = ROOT / "evidence/remote-control/queue-state.json"
if terminal_path.exists() and json.loads(terminal_path.read_text()).get("phase") == "complete":
    assert all(audits[number]["covered"] == 64 for number in ["2880", "2881", "2882"]), "Final Qwen pairing/identity audit failed"
    assert all(block["status"] == "verified" for block in audits["2859"]["blocks"]), "Final MOSS pairing/quality/cost audit failed"
    assert review["status"] == "verified", "Additional review validation or saved transcript differences are incomplete"
