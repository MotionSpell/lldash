import argparse
import threading
import subprocess
import time
import cwipc

def run_server(args: argparse.Namespace):
    if args.verbose:
        print("Starting server...")
    subprocess.run(["evanescent.exe", "--port", "9000"])

def run_sender(args: argparse.Namespace):
    if args.verbose:
        print("Starting sender...")
    subprocess.run(["cwipc_forward", "--count", "100", "--verbose", "--synthetic", "--nodrop", "--bin2dash", "http://127.0.0.1:9000/"])

def run_receiver(args: argparse.Namespace):
    if args.verbose:
        print("Sleep 5 seconds")
    time.sleep(5)
    if args.verbose:
        print("Starting receiver...")
    subprocess.run(["cwipc_view", "--verbose", "--nodisplay", "--sub", "http://127.0.0.1:9000/bin2dashSink.mpd"])


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
        server_thread = threading.Thread(target=run_server, args=(args,))
        sender_thread = threading.Thread(target=run_sender, args=(args,))
        receiver_thread = threading.Thread(target=run_receiver, args=(args,))
        if args.verbose:
            print("Starting threads...")
        server_thread.start()
        sender_thread.start()
        receiver_thread.start()
        if args.verbose:
            print("Waiting for threads to finish...")
        server_thread.join()
        sender_thread.join()
        receiver_thread.join()
    else:
        print("Invalid mode selected. Use --help for more information.")
        return

if __name__ == "__main__":
    main()