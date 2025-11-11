import threading
import argparse
import subprocess
import sys
from typing import Optional

class ServerThread(threading.Thread):
    def __init__(self, args: argparse.Namespace):
        super().__init__(daemon=True)
        self.name = "testlatency.ServerThread"
        self.args = args
        self.process : Optional[subprocess.Popen[str]] = None
        self.exit_status = -1
        self.did_terminate = False

    def run(self):
        serverproc_stderr = None
        serverproc_stdout = None
        if self.args.logdir:
            serverproc_stderr = open(self.args.logdir + "/testlatency_server.stderr.log", "w")
            serverproc_stdout = open(self.args.logdir + "/testlatency_server.stdout.log", "w")
        if self.args.verbose:
            print("testlatency: server: Starting server...", file=sys.stderr)
        cmdline = [
            "lldash-relay.exe", 
            "--port", "9000"
        ]
        if self.args.long_poll:
            cmdline += ["--long-poll", str(self.args.long_poll)]
        self.process = subprocess.Popen(
            cmdline,
            text=True,
            stdout=serverproc_stdout,
            stderr=serverproc_stderr
        )

        self.exit_status = self.process.wait()
        if self.args.verbose:
            print("testlatency: server: Server finished with exit status:", self.exit_status, file=sys.stderr)
        if self.did_terminate:
            # Expected exit status for SIGTERM, or 1 on Windows.
            self.exit_status = 0
        
    def stop(self):
        if self.process:
            self.did_terminate = True
            if self.args.verbose:
                print("testlatency: server: Killing server...", file=sys.stderr)
            self.process.terminate()
            
