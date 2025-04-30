import threading
import argparse
import subprocess
import sys
import time
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
            print("testlatency: server: Starting server...", file=sys.stderr)
        self.process = subprocess.Popen(
            [
                "evanescent.exe", 
                "--port", "9000"
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        reported_mpd_seen = False
        while True:
            assert self.process.stdout
            line = self.process.stdout.readline()
            if not line:
                break
            line = line.strip()
            if self.args.verbose:
                print(f"testlatency: server: Server output: {line}", file=sys.stderr)
            if not reported_mpd_seen and "Added" in line and ".mpd" in line:
                if self.args.verbose:
                    print(f"testlatency: server: MPD file seen in server output: {line}", file=sys.stderr)
                self.mpd_seen.release()
                reported_mpd_seen = True
        self.exit_status = self.process.wait()
        if self.args.verbose:
            print("testlatency: server: Server finished with exit status:", self.exit_status, file=sys.stderr)
        if self.exit_status == -15:
            # Expected exit status for SIGTERM
            self.exit_status = 0
        
    def stop(self):
        if self.process:
            self.process.terminate()
            
    def wait_for_mpd(self, timeout : float = 0) -> bool:
        # Alternative implementation: we wait for 2* seg_dur
        wait_dur = 4 * self.args.seg_dur
        time.sleep(wait_dur / 1000.0)
        return True
        ok = self.mpd_seen.acquire(timeout=timeout)
        if not ok:
            print("testlatency: server: MPD file not seen in server output, aborting...", file=sys.stderr)
            return False
        if self.args.verbose:
            print("testlatency: server: MPD file seen, continuing...", file=sys.stderr)
        return True        