import threading
import argparse
import subprocess
import sys
from typing import Optional

class ServerThread(threading.Thread):
    def __init__(self, args: argparse.Namespace):
        super().__init__()
        self.args = args
        self.process : Optional[subprocess.Popen[str]] = None
        self.mpd_seen = threading.Semaphore(0)
        self.exit_status = -1

    def run(self):
        if self.args.verbose:
            print("testlatency: Starting server...", file=sys.stderr)
        self.process = subprocess.Popen(
            [
                "evanescent.exe", 
                "--port", "9000"
            ],
            text=True,
            stdout=subprocess.PIPE,
        )
        reported_mpd_seen = False
        while True:
            assert self.process.stdout
            line = self.process.stdout.readline()
            if not line:
                break
            line = line.strip()
            if self.args.verbose:
                print(f"testlatency: Server output: {line}", file=sys.stderr)
            if not reported_mpd_seen and "Added" in line and ".mpd" in line:
                if self.args.verbose:
                    print(f"testlatency: MPD file seen in server output: {line}", file=sys.stderr)
                self.mpd_seen.release()
                reported_mpd_seen = True
        self.exit_status = self.process.wait()
        if self.args.verbose:
            print("testlatency: Server finished with exit status:", self.exit_status, file=sys.stderr)
        if self.exit_status == -15:
            # Expected exit status for SIGTERM
            self.exit_status = 0
        
    def stop(self):
        if self.process:
            self.process.terminate()
            
    def wait_for_mpd(self, timeout : float):
        self.mpd_seen.acquire(timeout=timeout)
        if self.args.verbose:
            print("testlatency: MPD file seen, continuing...", file=sys.stderr)
        