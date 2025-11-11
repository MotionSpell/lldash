import argparse
import threading
import sys
import time
from typing import Optional, NamedTuple, List
import cwipc
from cwipc.net.abstract import cwipc_sink_abstract, cwipc_rawsink_abstract
import cwipc.net.sink_lldpkg
import cwipc.net.sink_encoder
import cwipc.net.sink_passthrough


class SenderStatistics(NamedTuple):
    timestamp : float
    sender_wallclock : float
    sender_num : int
    sender_count : int

class SenderThread(threading.Thread):

    def __init__(self, args : argparse.Namespace):
        super().__init__(daemon=True)
        self.name = "testlatency.SenderThread"
        self.args = args
        self.exit_status = -1
        self.alive = True
        self.source : Optional[cwipc.cwipc_tiledsource_wrapper] = None
        self.encoder : Optional[cwipc_sink_abstract] = None
        self.sender : Optional[cwipc_rawsink_abstract] = None
        self.statistics : List[SenderStatistics] = []
        self.stop_requested = False

    def init(self):
        npoints = self.args.npoints
        url = "http://127.0.0.1:9000/lldash_testlatency.mpd"
        nodrop = True
        if self.args.debug:
            print(f"testlatency: sender: creating cwipc_sink_lldpkg({url}, ...)", file=sys.stderr)
        self.sender = cwipc.net.sink_lldpkg.cwipc_sink_lldpkg(url, self.args.debug, nodrop, seg_dur_in_ms=self.args.seg_dur)
        if self.args.debug:
            print(f"testlatency: sender: created cwipc_sink_lldpkg({url}, ...)", file=sys.stderr)
        if self.args.uncompressed:
            self.encoder = cwipc.net.sink_passthrough.cwipc_sink_passthrough(self.sender, self.args.debug, nodrop)
        else:
            self.encoder = cwipc.net.sink_encoder.cwipc_sink_encoder(self.sender, self.args.debug, nodrop)
        self.source = cwipc.cwipc_synthetic(self.args.fps, npoints)
        
        self.encoder.set_producer(self)

        # self.sender.start()
        self.encoder.start()
        if self.args.debug:
            print("testlatency: Sender initialized.", file=sys.stderr)
            
    def is_alive(self):
        return self.alive
    
    def stop(self):
        self.stop_requested = True

    def close(self):
        self.alive = False
        if self.args.verbose:
            if self.encoder:
                self.encoder.statistics()
            if self.sender:
                self.sender.statistics()
        # self.source.stop()
        # self.sender.stop()
        if self.encoder:
            self.encoder.stop()
            # self.encoder.free()
        self.encoder = None
        if self.source:
            self.source.free()
        self.source = None
        self.sender = None
        
    def report(self, num : int, timestamp : float, count : int):
        now = time.time()
        if self.args.verbose:
            print(f"testlatency: sender: now={now}, timestamp={timestamp}, sender_num={num}, sender_pointcount={count}", file=sys.stderr)
        self.statistics.append(SenderStatistics(timestamp, now, num, count))
        
    def run(self):
        if self.args.debug:
            print("testlatency: Starting sender...", file=sys.stderr)
        self.init()
        assert self.source
        assert self.encoder
        assert self.sender
        start_time = time.time()
        num = 0
        self.exit_status = 0
        while time.time() - start_time < self.args.duration and not self.stop_requested:
            ok = self.source.available(wait=True)
            if not ok:
                print("testlatency: Sender source not available, exiting...", file=sys.stderr)
                self.exit_status = 1
                break
            pc = self.source.get()
            if pc is None:
                print("testlatency: Sender source returned None, exiting...", file=sys.stderr)
                self.exit_status = 1
                break
            self.report(num, pc.timestamp(), pc.count())
            self.encoder.feed(pc)
            num += 1
        if self.args.verbose:
            print(f"testlatency: sent {num} point clouds in {time.time()-start_time} seconds.", file=sys.stderr)
        self.close()

        if self.args.debug:
            print("testlatency: Sender finished with exit status:", self.exit_status, file=sys.stderr)
