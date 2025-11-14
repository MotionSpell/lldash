
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
import cwipc.net.source_synchronizer
from typing import Optional, NamedTuple, List

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
        self.needs_synchronizer = self.args.tiled or self.args.synchronizer
        self.pc_source : Optional[cwipc_source_abstract] = None
        self.statistics : list[ReceiverStatistics] = []
        self.stop_requested = False
        self.last_timestamp : Optional[int] = None

    def init(self):
        url = "http://127.0.0.1:9000/lldash_testlatency.mpd"
        if self.args.uncompressed:
            decoder_factory = cwipc.net.source_passthrough.cwipc_source_passthrough
        else:
            decoder_factory = cwipc.net.source_decoder.cwipc_source_decoder
        
        if self.needs_synchronizer:
            raw_multisource = cwipc.net.source_lldplay.cwipc_multisource_lldplay(url, verbose=self.args.debug)
            n_tile = raw_multisource.get_tile_count()
            if self.args.verbose:
                print(f"testlatency: receiver: multisource has {n_tile} tiles", file=sys.stderr)
            decoders : List[cwipc_source_abstract] = []
            for i in range(n_tile):
                raw_source = raw_multisource.get_tile_source(i)
                decoder = decoder_factory(raw_source, verbose=self.args.debug)
                decoders.append(decoder)
            self.pc_source = cwipc.net.source_synchronizer.cwipc_source_synchronizer(raw_source, decoders, verbose=self.args.debug)
        else:
            raw_source = cwipc.net.source_lldplay.cwipc_source_lldplay(url, verbose=self.args.debug)
            self.pc_source = decoder_factory(raw_source, verbose=self.args.debug)
        assert self.pc_source
        self.pc_source.start()

    def stop(self):
        self.stop_requested = True

    def close(self):
        if self.args.verbose:
            self.pc_source.statistics()
        if self.pc_source:
            self.pc_source.stop()
            self.pc_source.free()
            self.pc_source = None

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
        assert self.pc_source
        start_time = time.time()
        num = 0
        self.exit_status = 0
        while not self.pc_source.eof() and not self.stop_requested:
            if not self.pc_source.available(True):
                continue
            pc = self.pc_source.get()
            if pc == None:
                if not self.pc_source.eof():
                    print("testlatency: receiver: No point cloud received but not eof(), aborting...", file=sys.stderr)
                    self.exit_status = -1
                break
            self.report(num, pc.timestamp(), pc.count())
            num += 1
        if self.args.verbose:
            print(f"testlatency: receiver: Received {num} point clouds in {time.time() - start_time} seconds", file=sys.stderr)
        self.close()
