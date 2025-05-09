import sys
import argparse
import threading
import subprocess
from typing import Optional
import cwipc
from testlatency_server import ServerThread
from testlatency_sender import SenderThread, SenderStatistics
from testlatency_receiver import ReceiverThread, ReceiverStatistics
from testlatency_analyse import Analyser, AnalyserResults

def main():
    parser = argparse.ArgumentParser(description="Test latency of CWIPC.")
    parser.add_argument(
        "--mode",
        choices=["server", "sender", "receiver", "all"],
        default="all",
        help="Mode to run the script in: server, sender, or receiver. Default: all",
    )
    parser.add_argument(
        "--fps",
        type=int,
        default=0,
        help="Frames per second for the synthetic source. Default is leave to capturer.",)
    parser.add_argument(
        "--npoints",
        type=int,
        default=0,
        help="Number of points for the synthetic source. Default is leave to capturer.",)
    parser.add_argument(
        "--uncompressed",
        action="store_true",
        help="Use uncompressed point clouds.",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=20,
        help="Duration in seconds for the sender. Default is 20.",
    )
    parser.add_argument(
        "--all_latencies",
        action="store_true",
        help="Don't ignore initial latencies in the analysis.",
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
    parser.add_argument(
        "--logdir",
        type=str,
        default="",
        help="Directory to store log files. Default: on stdout and stderr",
    )
    parser.add_argument(
        "--debugpy",
        action="store_true",
        help="Enable debugpy for remote debugging.",
    )
    args = parser.parse_args()

    if args.debugpy:
        import debugpy
        debugpy.listen(5678)
        print(f"{sys.argv[0]}: waiting for debugpy attach on 5678", flush=True)
        debugpy.wait_for_client()
        print(f"{sys.argv[0]}: debugger attached")        
    if args.logdir:
        import os
        if not os.path.exists(args.logdir):
            os.makedirs(args.logdir)
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
        #
        # Wait for the MPD to be produced, so we know we can start the receiver.
        #
        ok = server_thread.wait_for_mpd(10)
        if not ok:
            print("testlatency: Server thread did not produce MPD file in 10 seconds, aborting...", file=sys.stderr)
            server_thread.stop()
            sender_thread.stop()
        #
        # Check that the sender and server thread are still alive
        #
        if not sender_thread.is_alive():
            print("testlatency: Sender thread appears to have stopped", file=sys.stderr)
            ok = False
        if not server_thread.is_alive():
            print("testlatency: Server thread appears to have stopped", file=sys.stderr)
            ok = False
        #
        # Start the receiver
        #
        if ok:
            if args.verbose:
                print("testlatency: Starting receiver thread...", file=sys.stderr)
            receiver_thread.start()
        else:
            print("testlatency: Skip receiver thread start, stop sender and server threads", file=sys.stderr)
            sender_thread.stop()
            receiver_thread.stop()
        if args.verbose:
            print("testlatency: Waiting for threads to finish...", file=sys.stderr)
        if sender_thread.is_alive():
            sender_thread.join()
        if args.verbose:
            print("testlatency: sender thread finished", file=sys.stderr)
        if receiver_thread.is_alive():
            receiver_thread.join()
        if args.verbose:
            print("testlatency: receiver thread finished", file=sys.stderr)
        if server_thread.is_alive():
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
        if not ok:
            print(f"testlatency: One or more threads exited with an error.")
            print(f"testlatency: results are probably bogus.")
        analyser = Analyser(receiver_thread.statistics, sender_thread.statistics)
        results = analyser.analyse(not args.all_latencies)
        analyser.print(results)
        if ok and analyser.judge(results):
            print("testlatency: Latency test passed.")
            return 0
        else:
            print("testlatency: Latency test failed.")
            return 1
    else:
        print("testlatency: Invalid mode selected. Use --help for more information.", file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())