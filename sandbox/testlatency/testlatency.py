import argparse
import threading
import subprocess
import time
import cwipc

class ServerThread(threading.Thread):
    def __init__(self, args: argparse.Namespace):
        super().__init__()
        self.args = args
        self.process = None

    def run(self):
        if self.args.verbose:
            print("Starting server...")
        outfile = open("testlatency_server_output.txt", "w")
        self.process = subprocess.Popen(
            [
                "evanescent.exe", 
                "--port", "9000"
            ],
            stdout=outfile,
            stderr=subprocess.STDOUT,
        )
        self.process.wait()
        
    def stop(self):
        if self.process:
            self.process.terminate()
        
class SenderThread(threading.Thread):
    def __init__(self, args : argparse.Namespace):
        super().__init__()
        self.args = args

    def run(self):
        if self.args.verbose:
            print("Starting sender...")
        outfile = open("testlatency_sender_output.txt", "w")
        subprocess.run(
            [
                "cwipc_forward", 
                "--count", "100", 
                "--verbose", 
                "--synthetic", 
                "--nodrop", 
                "--bin2dash", "http://127.0.0.1:9000/", 
                "--seg_dur", "2000"
        ],
        stdout=outfile,
        stderr=subprocess.STDOUT,
    )

class ReceiverThread(threading.Thread):
    def __init__(self, args: argparse.Namespace):
        super().__init__()
        self.args = args

    def run(self):
        if self.args.verbose:
            print("Starting receiver...")
        outfile = open("testlatency_receiver_output.txt", "w")
        subprocess.run(
            [
                "cwipc_view", 
                "--verbose", 
                "--nodisplay", 
                "--sub", "http://127.0.0.1:9000/bin2dashSink.mpd"
        ],
        stdout=outfile,
        stderr=subprocess.STDOUT,
    )

def main():
    parser = argparse.ArgumentParser(description="Test latency of CWIPC.")
    parser.add_argument(
        "--mode",
        choices=["server", "sender", "receiver", "all"],
        default="all",
        help="Mode to run the script in: server, sender, or receiver.",
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
        run_server(args)
    elif args.mode == "sender":
        run_sender(args)
    elif args.mode == "receiver":
        run_receiver(args)
    elif args.mode == "all":
        server_thread = ServerThread(args)
        sender_thread = SenderThread(args)
        receiver_thread = ReceiverThread(args)
        if args.verbose:
            print("Starting threads...")
        server_thread.start()
        sender_thread.start()
        receiver_thread.start()
        if args.verbose:
            print("Waiting for threads to finish...")
        sender_thread.join()
        if args.verbose:
            print("sender thread finished")
        receiver_thread.join()
        if args.verbose:
            print("receiver thread finished")
        if args.verbose:
            print("Stopping server thread...")
        server_thread.stop()
        server_thread.join()
        if args.verbose:
            print("server thread finished")
        
    else:
        print("Invalid mode selected. Use --help for more information.")
        return

if __name__ == "__main__":
    main()