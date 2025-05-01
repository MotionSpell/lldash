
import argparse
import subprocess
import threading
import sys


class ReceiverThread(threading.Thread):
    def __init__(self, args: argparse.Namespace):
        super().__init__()
        self.args = args
        self.exit_status = -1

    def run(self):
        if self.args.verbose:
            print("testlatency: Starting receiver...", file=sys.stderr)
        result = subprocess.run(
            [
                "cwipc_view", 
                "--nodisplay", 
                "--sub", "http://127.0.0.1:9000/bin2dashSink.mpd"
            ],
            check=True,
        )
        self.exit_status = result.returncode
        if self.args.verbose:
            print("testlatency: Receiver finished with exit status:", self.exit_status, file=sys.stderr)
