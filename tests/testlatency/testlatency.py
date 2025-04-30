import sys
import argparse
import threading
import subprocess
from typing import Optional
import cwipc

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
        result = subprocess.run(
            cmd_line,
            check=True
        )
        self.exit_status = result.returncode
        if self.args.verbose:
            print("testlatency: Sender finished with exit status:", self.exit_status, file=sys.stderr)

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

def main():
    parser = argparse.ArgumentParser(description="Test latency of CWIPC.")
    parser.add_argument(
        "--mode",
        choices=["server", "sender", "receiver", "all"],
        default="all",
        help="Mode to run the script in: server, sender, or receiver.",
    )
    parser.add_argument(
        "--seg_dur",
        type=int,
        default=0,
        help="Segment duration in milliseconds. Default is leave to lldash-srd-packager.",
    )
    parser.add_argument(
        "--server_host",
        type=str,
        default="localhost",
        help="Host address for the server.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output.",
    )
    args = parser.parse_args()

    if args.mode == "server":
        ServerThread(args).run()
    elif args.mode == "sender":
        SenderThread(args).run()
    elif args.mode == "receiver":
        ReceiverThread(args).run()
    elif args.mode == "all":
        server_thread = ServerThread(args)
        sender_thread = SenderThread(args)
        receiver_thread = ReceiverThread(args)
        if args.verbose:
            print("testlatency: Starting server and sender threads...", file=sys.stderr)
        server_thread.start()
        sender_thread.start()
        server_thread.wait_for_mpd(10)
        if args.verbose:
            print("testlatency: Starting receiver thread...", file=sys.stderr)
        receiver_thread.start()
        if args.verbose:
            print("testlatency: Waiting for threads to finish...", file=sys.stderr)
        sender_thread.join()
        if args.verbose:
            print("testlatency: sender thread finished", file=sys.stderr)
        receiver_thread.join()
        if args.verbose:
            print("testlatency: receiver thread finished", file=sys.stderr)
        if args.verbose:
            print("testlatency: Stopping server thread...", file=sys.stderr)
        server_thread.stop()
        server_thread.join()
        if args.verbose:
            print("testlatency: server thread finished", file=sys.stderr)
        ok = True
        if server_thread.exit_status != 0:
            print(f"testlatency: Server thread exited with exit status code {server_thread.exit_status}", file=sys.stderr)
            ok = False
        if sender_thread.exit_status != 0:
            print(f"testlatency: Sender thread exited with exit status code {sender_thread.exit_status}", file=sys.stderr)
            ok = False
        if receiver_thread.exit_status != 0:
            print(f"testlatency: Receiver thread exited with exit status code {receiver_thread.exit_status}", file=sys.stderr)
            ok = False
        if ok:
            return 0
        else:
            print(f"testlatency: One or more threads exited with an error.", file=sys.stderr)
            sys.exit(1)
    else:
        print("testlatency: Invalid mode selected. Use --help for more information.", file=sys.stderr)
        return -1

if __name__ == "__main__":
    main()