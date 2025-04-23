import argparse
import threading
import cwipc

def run_server(args: argparse.Namespace):
    if args.verbose:
        print("Starting server...")
    # Placeholder for server logic

def run_sender(args: argparse.Namespace):
    if args.verbose:
        print("Starting sender...")
    # Placeholder for sender logic

def run_receiver(args: argparse.Namespace):
    if args.verbose:
        print("Starting receiver...")
    # Placeholder for receiver logic
    

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

        server_thread.start()
        sender_thread.start()
        receiver_thread.start()

        server_thread.join()
        sender_thread.join()
        receiver_thread.join()

if __name__ == "__main__":
    main()