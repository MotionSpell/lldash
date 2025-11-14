
import argparse
import threading
import sys
import time
from collections import namedtuple
import cwipc
from cwipc.net.abstract import cwipc_rawmultisource_abstract, cwipc_source_abstract
import cwipc.net.source_passthrough
import cwipc.net.source_lldplay
import cwipc.net.source_decoder
import cwipc.net.source_synchronizer
from typing import Optional, NamedTuple, List, Dict, Any

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
        self.raw_multisource : Optional[cwipc_rawmultisource_abstract] = None
        self.statistics : List[ReceiverStatistics] = []
        self.n_tile : int = 1
        self.n_quality : int = 1
        self.cur_quality : int = 0
        self.stop_requested = False
        self.last_timestamp : Optional[int] = None
        self.next_quality_switch_time : Optional[float] = None

    def init(self):
        url = "http://127.0.0.1:9000/lldash_testlatency.mpd"
        if self.args.uncompressed:
            decoder_factory = cwipc.net.source_passthrough.cwipc_source_passthrough
        else:
            decoder_factory = cwipc.net.source_decoder.cwipc_source_decoder
        
        if self.needs_synchronizer:
            self.raw_multisource = cwipc.net.source_lldplay.cwipc_multisource_lldplay(url, verbose=self.args.debug)
            self.n_tile = self.raw_multisource.get_tile_count()
            if self.args.verbose:
                print(f"testlatency: receiver: multisource has {self.n_tile} tiles", file=sys.stderr)
            description = self.raw_multisource.get_description()
            self.n_quality = len(description[0])
            if self.args.verbose:
                print(f"testlatency: receiver: multisource has {self.n_quality} qualities", file=sys.stderr)
            decoders : List[cwipc_source_abstract] = []
            for i in range(self.n_tile):
                raw_source = self.raw_multisource.get_tile_source(i)
                decoder = decoder_factory(raw_source, verbose=self.args.debug)
                decoders.append(decoder)
            self.pc_source = cwipc.net.source_synchronizer.cwipc_source_synchronizer(self.raw_multisource, decoders, verbose=self.args.debug)
        else:
            raw_source = cwipc.net.source_lldplay.cwipc_source_lldplay(url, verbose=self.args.debug)
            self.pc_source = decoder_factory(raw_source, verbose=self.args.debug)
        assert self.pc_source
        self.pc_source.start()
        if self.args.switch_initial:
            self.switch_quality()
        if self.args.switch_interval:
            self.next_quality_switch_time = time.time() + self.args.switch_interval

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
            if self.next_quality_switch_time != None and time.time() > self.next_quality_switch_time:
                self.switch_quality()
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

    def switch_quality(self) -> None:
        next_qualIdx = (self.cur_quality + 1) % self.n_quality
        if next_qualIdx == self.cur_quality:
            print(f"testlatency: receiver: cannot switch: single quality source")
            return
        assert self.raw_multisource
        self.cur_quality = next_qualIdx
        if self.args.verbose:
            print(f"testlatency: receiver: select quality {self.cur_quality} for {self.n_tile} tiles", file=sys.stderr)
        for tileIdx in range(self.n_tile):
            self.raw_multisource.select_tile_quality(tileIdx, self.cur_quality)
        if self.args.switch_interval:
            self.next_quality_switch_time = time.time() + self.args.switch_interval
        