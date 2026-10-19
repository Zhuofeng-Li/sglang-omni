"""Persist per-seed metrics and pairing identities without copying generated audio."""
from collections import Counter
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re

ROOT = Path("/data/zhuofeng-li/home/omni-review-20261019")


def save(path, value):
    temporary = path.with_suffix(".partial")
    temporary.write_text(json.dumps(value, indent=2))
    temporary.replace(path)


for directory in (ROOT / "moss-results").glob("pr2859-*"):
    for kind in ["speed", "wer", "similarity"]:
        source = directory / f"{kind}_results.json"
        if not source.exists():
            continue
        try:
            value = json.loads(source.read_text())
        except json.JSONDecodeError:
            continue
        samples = value.get("per_request", value.get("per_sample", []))
        ids = [str(row.get("id")) for row in samples]
        output = {key: value[key] for key in ["summary", "config"] if key in value}
        output.update(sample_count=len(samples), sample_order_sha256=hashlib.sha256("\n".join(ids).encode()).hexdigest(), failures=[row for row in samples if row.get("is_success") is False])
        save(directory / f"{kind}-summary.json", output)
    captured = set()
    destroyed = set()
    callers = Counter()
    for path in (directory / "graphs").glob("graphs-*.jsonl"):
        for line in path.read_text().splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = (row["pid"], row["token"])
            if row["event"] == "captured":
                captured.add(key)
                callers[row["caller"]] += 1
            else:
                destroyed.add(key)
    save(directory / "graph-summary.json", {"successful_captures": len(captured), "live_at_export": len(captured - destroyed), "callers": callers, "note": "Export may run after shutdown; live_at_export is not a peak or post-scoring live count."})
    operator_log = directory / "operator.log"
    if operator_log.exists():
        launched = None
        ready = None
        for line in operator_log.read_text().splitlines():
            if "Starting server:" in line:
                launched = datetime.strptime(line[:23], "%Y-%m-%d %H:%M:%S,%f")
            elif "Service is ready." in line:
                ready = datetime.strptime(line[:23], "%Y-%m-%d %H:%M:%S,%f")
        if launched is not None and ready is not None:
            save(directory / "cost-summary.json", {"startup_seconds": (ready - launched).total_seconds(), "startup_method": "Timestamp immediately before server subprocess launch through health-ready, including model/graph initialization, excluding client imports/downloads and workload warmup.", "successful_captures": len(captured), "graph_method": "Unique successful capture events for this cohort; not post-shutdown live objects."})
