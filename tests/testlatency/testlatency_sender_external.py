
import subprocess
import argparse
import threading
import sys

class SenderThread(threading.Thread):
    def __init__(self, args : argparse.Namespace):
        super().__init__()
        self.args = args
        self.exit_status = -1

    def run(self):
        if self.args.verbose:
            print("testlatency: Starting sender...", file=sys.stderr)
        cmd_line = [
            "cwipc_forward", 
            "--verbose",
            "--count", "450",
            "--fps", "15", 
            "--synthetic", 
            "--bin2dash", "http://127.0.0.1:9000/", 
        ]
        if self.args.seg_dur > 0:
            cmd_line += ["--seg_dur", str(self.args.seg_dur)]
        if self.args.timeshift_buffer_ms > 0:
            cmd_line += ["--timeshift_buffer_ms", str(self.args.timeshift_buffer_ms)]
        result = subprocess.run(
            cmd_line,
            check=True
        )
        self.exit_status = result.returncode
        if self.args.verbose:
            print("testlatency: Sender finished with exit status:", self.exit_status, file=sys.stderr)
