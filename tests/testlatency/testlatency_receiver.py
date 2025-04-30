
import argparse
import subprocess
import threading
import sys
import time
import cwipc
import cwipc.net.source_sub
import cwipc.net.source_decoder
from typing import Optional


class ReceiverThread(threading.Thread):
    def __init__(self, args: argparse.Namespace):
        super().__init__()
        self.args = args
        self.exit_status = -1
        self.source : Optional[cwipc.net.cwipc_rawsource_abstract] = None
        self.decoder : Optional[cwipc.cwipc_decoder] = None

    def init(self):
        url = "http://127.0.0.1:9000/bin2dashSink.mpd"
        self.source = cwipc.net.source_sub.cwipc_source_sub(url, self.args.verbose)
        self.decoder = cwipc.net.source_decoder.cwipc_source_decoder(self.source, self.args.verbose)
        
        # self.source.start()
        self.decoder.start()

    def close(self):
        if self.args.verbose:
            self.source.statistics()
            self.decoder.statistics()
        # self.source.stop()
        self.decoder.stop()
        
        self.source.free()
        self.source = None
        self.decoder.free()
        self.decoder = None

    def report(self, num : int, timestamp : float, count : int):
        now = time.time()
        now_ms = int(now * 1000)
        latency = now_ms - timestamp
        if True:
            print(f"testlatency: receiver: now={now}, num={num}, timestamp={timestamp}, latency={latency}, pointcount={count}", file=sys.stderr)
        
    def run(self):
        if self.args.verbose:
            print("testlatency: Starting receiver...", file=sys.stderr)
        self.init()
        assert self.source
        assert self.decoder
        start_time = time.time()
        num = 0
        self.exit_status = 0
        while self.decoder.available(True):
            pc = self.decoder.get()
            if pc == None:
                print("testlatency: receiver: No point cloud received, aborting...", file=sys.stderr)
                self.exit_status = -1
                break
            self.report(num, pc.timestamp(), pc.count())
            num += 1
        if self.args.verbose:
            print(f"testlatency: receiver: Received {num} point clouds in {time.time() - start_time} seconds", file=sys.stderr)
        self.close()
