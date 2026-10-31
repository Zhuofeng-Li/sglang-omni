"""Count successful CUDA captures without changing tensor operations."""
import json
import os
from pathlib import Path
import runpy
import socket
import sys
import time
import traceback

if 'RSI_TTS_CLIENT_SOURCE' in os.environ:
    runpy.run_path('/tests/bootstrap/sitecustomize.py')
import torch

original_capture_end = torch.cuda.CUDAGraph.capture_end

def capture_end(graph):
    result = original_capture_end(graph)
    output = os.environ.get('MING_PR_GRAPH_EVENTS')
    if output:
        event = {'epoch':time.time(),'pid':os.getpid(),
                 'stack':[f.filename for f in traceback.extract_stack(limit=12)]}
        with Path(output).open('a') as stream:
            stream.write(json.dumps(event)+'\n')
    return result

torch.cuda.CUDAGraph.capture_end = capture_end

if '-m' in sys.orig_argv and sys.orig_argv[sys.orig_argv.index('-m')+1] == 'benchmarks.eval.benchmark_tts_seedtts':
    import psutil
    from benchmarks.benchmarker import utils as benchmark_utils

    native_stop_server = benchmark_utils.stop_server

    def stop_server_and_drain_port(process):
        native_stop_server(process)
        arguments = process.args
        if '--port' not in arguments:
            return
        port = int(arguments[arguments.index('--port')+1])
        deadline = time.monotonic()+90
        started = time.monotonic()
        waiting = False
        while True:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                    probe.bind(('localhost',port))
                if waiting:
                    print(json.dumps({'operator_port_drain_seconds':time.monotonic()-started,'port':port}),flush=True)
                return
            except OSError as error:
                connections = [connection for connection in psutil.net_connections(kind='tcp') if connection.laddr and connection.laddr.port==port]
                states = sorted({connection.status for connection in connections})
                if error.errno!=98 or 'LISTEN' in states or time.monotonic()>=deadline:
                    raise
                if not waiting:
                    print(json.dumps({'operator_waiting_for_released_port':port,'socket_states':states}),flush=True)
                    waiting = True
                time.sleep(.25)

    benchmark_utils.stop_server = stop_server_and_drain_port

