import threading
import argparse
import subprocess
import sys
import time
from typing import Optional

class ServerThread(threading.Thread):
    def __init__(self, args: argparse.Namespace):
        super().__init__()
        self.name = "testlatency.ServerThread"
        self.args = args
        self.process : Optional[subprocess.Popen[str]] = None
        self.mpd_seen = threading.Semaphore(0)
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
            "evanescent.exe", 
            "--port", "9000"
        ]
        if self.args.long_poll:
            cmdline += ["--long-poll", str(self.args.long_poll)]
        self.process = subprocess.Popen(
            cmdline,
            text=True,
            stdout=serverproc_stdout,
            stderr=subprocess.PIPE
        )
        reported_mpd_seen = False
        while True:
            assert self.process.stderr
            line = self.process.stderr.readline()
            if not line:
                break
            if serverproc_stderr:
                serverproc_stderr.write(line)
            line = line.strip()
            if self.args.verbose:
                print(f"testlatency: server: Server output: {line}", file=sys.stderr)
            if not reported_mpd_seen and "method=PUT" in line and ".mpd" in line:
                if self.args.verbose:
                    print(f"testlatency: server: MPD file seen in server output: {line}", file=sys.stderr)
                self.mpd_seen.release()
                reported_mpd_seen = True
        self.exit_status = self.process.wait()
        if self.args.verbose:
            print("testlatency: server: Server finished with exit status:", self.exit_status, file=sys.stderr)
        if self.did_terminate:
            # Expected exit status for SIGTERM, or 1 on Windows.
            self.exit_status = 0
        
    def stop(self):
        if self.process:
            self.did_terminate = True
            self.process.terminate()
            
    def wait_for_mpd(self, timeout : Optional[float] = None) -> bool:
        ok = self.mpd_seen.acquire(timeout=timeout)
        if not ok:
            print("testlatency: server: MPD file not seen in server output, aborting...", file=sys.stderr)
            return False
        if self.args.verbose:
            print("testlatency: server: MPD file seen, continuing...", file=sys.stderr)
        return True        