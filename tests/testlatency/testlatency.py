import sys
import argparse
import threading
import subprocess
from typing import Optional
import cwipc
from testlatency_server import ServerThread
from testlatency_sender import SenderThread
from testlatency_receiver import ReceiverThread


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