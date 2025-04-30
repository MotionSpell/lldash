import argparse
import threading
import sys
import time
from typing import Optional
import cwipc
import cwipc.net.sink_bin2dash
import cwipc.net.sink_encoder

class SenderThread(threading.Thread):
    def __init__(self, args : argparse.Namespace):
        super().__init__()
        self.args = args
        self.exit_status = -1
        self.alive = True
        self.source : Optional[cwipc.cwipc_tiledsource_wrapper] = None
        self.encoder : Optional[cwipc.cwipc_encoder] = None
        self.sender : Optional[cwipc.net.cwipc_rawsink_abstract] = None

    def init(self):
        npoints = 0
        url = "http://127.0.0.1:9000/"
        nodrop = True
        
        self.sender = cwipc.net.sink_bin2dash.cwipc_sink_bin2dash(url, self.args.verbose, nodrop, seg_dur_in_ms=self.args.seg_dur)
        self.encoder = cwipc.net.sink_encoder.cwipc_sink_encoder(self.sender, self.args.verbose, nodrop)
        self.source = cwipc.cwipc_synthetic(self.args.fps, npoints)
        
        self.encoder.set_producer(self)

        # self.sender.start()
        self.encoder.start()
        if self.args.verbose:
            print("testlatency: Sender initialized.", file=sys.stderr)
            
    def is_alive(self):
        return self.alive
    
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
        if self.args.verbose:
            print(f"testlatency: sender: now={time.time()}, num={num}, timestamp={timestamp}, pointcount={count}", file=sys.stderr)
            
    def run(self):
        self.init()
        if self.args.verbose:
            print("testlatency: Starting sender...", file=sys.stderr)
        assert self.source
        assert self.encoder
        assert self.sender
        count = 30
        num = 0
        self.exit_status = 0
        for num in range(count):
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
            count -= 1
        self.close()

        if self.args.verbose:
            print("testlatency: Sender finished with exit status:", self.exit_status, file=sys.stderr)
