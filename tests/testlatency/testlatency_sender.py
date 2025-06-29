import argparse
import threading
import sys
import time
from typing import Optional
from collections import namedtuple
import cwipc
import cwipc.net.sink_bin2dash
import cwipc.net.sink_encoder
import cwipc.net.sink_passthrough

SenderStatistics = namedtuple("SenderStatistics", ["timestamp", "sender_wallclock", "sender_num", "sender_count"])

class SenderThread(threading.Thread):
    def __init__(self, args : argparse.Namespace):
        super().__init__(daemon=True)
        self.name = "testlatency.SenderThread"
        self.args = args
        self.exit_status = -1
        self.alive = True
        self.source : Optional[cwipc.cwipc_tiledsource_wrapper] = None
        self.encoder : Optional[cwipc.cwipc_encoder] = None
        self.sender : Optional[cwipc.net.cwipc_rawsink_abstract] = None
        self.statistics : List[SenderStatistics] = []
        self.stop_requested = False

    def init(self):
        npoints = self.args.npoints
        url = "http://127.0.0.1:9000/"
        nodrop = True
        if self.args.debug:
            print(f"testlatency: sender: creating cwipc_sink_bin2dash({url}, ...)", file=sys.stderr)
        self.sender = cwipc.net.sink_bin2dash.cwipc_sink_bin2dash(url, self.args.debug, nodrop, seg_dur_in_ms=self.args.seg_dur)
        if self.args.debug:
            print(f"testlatency: sender: created cwipc_sink_bin2dash({url}, ...)", file=sys.stderr)
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
            self.encoder.statistics()
            self.sender.statistics()
        # self.source.stop()
        # self.sender.stop()
        self.encoder.stop()
        
        
        self.source.free()
        self.source = None
        # self.encoder.free()
        self.encoder = None
        self.sender.free()
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
