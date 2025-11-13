
import argparse
import threading
import sys
import time
from collections import namedtuple
import cwipc
from cwipc.net.abstract import cwipc_rawsource_abstract, cwipc_source_abstract
import cwipc.net.source_passthrough
import cwipc.net.source_lldplay
import cwipc.net.source_decoder
from typing import Optional, NamedTuple

class ReceiverStatistics(NamedTuple):
    timestamp : int
    receiver_wallclock : float
    receiver_num : int
    receiver_count : int
class ReceiverThread(threading.Thread):
    def __init__(self, args: argparse.Namespace):
        super().__init__(daemon=True)
        self.name = "testlatency.ReceiverThread"
        self.args = args
        self.exit_status = -1
        self.source : Optional[cwipc_rawsource_abstract] = None
        self.decoder : Optional[cwipc_source_abstract] = None
        self.statistics : list[ReceiverStatistics] = []
        self.stop_requested = False
        self.last_timestamp : Optional[int] = None

    def init(self):
        url = "http://127.0.0.1:9000/lldash_testlatency.mpd"
        self.source = cwipc.net.source_lldplay.cwipc_source_lldplay(url, verbose=self.args.debug)
        if self.args.uncompressed:
            self.decoder = cwipc.net.source_passthrough.cwipc_source_passthrough(self.source, verbose=self.args.debug)
        else:
            self.decoder = cwipc.net.source_decoder.cwipc_source_decoder(self.source, verbose=self.args.debug)
        
        assert self.decoder
        if hasattr(self.decoder, 'start'):
            self.decoder.start()
        else:
            self.source.start()

    def stop(self):
        self.stop_requested = True

    def close(self):
        if self.args.verbose:
            assert self.source
            self.source.statistics()
            if hasattr(self.decoder, 'statistics'):
                self.decoder.statistics()
        # self.source.stop()
        if self.decoder and hasattr(self.decoder, 'stop'):
            self.decoder.stop()
        
        if self.source and hasattr(self.source, 'free'):
            self.source.free()
        self.source = None
        self.decoder.free()
        self.decoder = None

    def report(self, num : int, timestamp_ms : int, count : int):
        now = time.time()
        now_ms = int(now * 1000)
        latency = now_ms - timestamp_ms
        if self.last_timestamp == None:
            self.last_timestamp = timestamp_ms
        delta = timestamp_ms - self.last_timestamp
        if self.args.verbose:
            print(f"testlatency: receiver: now={now}, timestamp={timestamp_ms}, receiver_num={num}, receiver_pointcount={count}, latency={latency}, delta={delta}", file=sys.stderr)
        self.last_timestamp = timestamp_ms
        self.statistics.append(ReceiverStatistics(timestamp_ms, now, num, count))
        
    def run(self):
        if self.args.debug:
            print("testlatency: Starting receiver...", file=sys.stderr)
        self.init()
        assert self.source
        assert self.decoder
        start_time = time.time()
        num = 0
        self.exit_status = 0
        while not self.decoder.eof() and not self.stop_requested:
            if not self.decoder.available(True):
                continue
            pc = self.decoder.get()
            if pc == None:
                if not self.decoder.eof():
                    print("testlatency: receiver: No point cloud received but not eof(), aborting...", file=sys.stderr)
                    self.exit_status = -1
                break
            self.report(num, pc.timestamp(), pc.count())
            num += 1
        if self.args.verbose:
            print(f"testlatency: receiver: Received {num} point clouds in {time.time() - start_time} seconds", file=sys.stderr)
        self.close()
