"""Identical capture telemetry for both benchmark arms."""
import itertools
import json
import os
import time
import traceback
import weakref

if os.environ.get("QUAL_GRAPH_DIR"):
    import torch

    COUNTER = itertools.count()
    ORIGINAL_END = torch.cuda.CUDAGraph.capture_end
    DIRECTORY = os.environ["QUAL_GRAPH_DIR"]
    os.makedirs(DIRECTORY, exist_ok=True)
    PATH = os.path.join(DIRECTORY, f"graphs-{os.getpid()}.jsonl")

    def record(event, token, caller=""):
        row = json.dumps({"event": event, "token": token, "pid": os.getpid(), "time": time.time(), "caller": caller}) + "\n"
        descriptor = os.open(PATH, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        try:
            os.write(descriptor, row.encode())
        finally:
            os.close(descriptor)

    def captured(self):
        result = ORIGINAL_END(self)
        token = next(COUNTER)
        frames = traceback.extract_stack(limit=8)
        caller = ";".join(f"{f.filename}:{f.name}" for f in frames[:-1])
        record("captured", token, caller)
        weakref.finalize(self, record, "destroyed", token)
        return result

    torch.cuda.CUDAGraph.capture_end = captured
