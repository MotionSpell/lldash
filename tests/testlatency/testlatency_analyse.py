import sys
from collections import namedtuple
import statistics
from testlatency_receiver import ReceiverStatistics
from testlatency_sender import SenderStatistics

AnalyserResults = namedtuple("AnalyserResults", ["count_total", "count_lost", "latency_min", "latency_max", "latency_avg", "latency_stddev"])
class Analyser:
    def __init__(self, receiver_statistics: list[ReceiverStatistics], sender_statistics: list[SenderStatistics]):
        self.receiver_statistics = receiver_statistics
        self.sender_statistics = sender_statistics
        
    def _gendicts(self):
        self.receiver_dict : dict[float, ReceiverStatistics] = {}
        self.sender_dict : dict[float, SenderStatistics] = {}
        for stat in self.receiver_statistics:
            if stat.timestamp in self.receiver_dict:
                print(f"testlatency: duplicate receiver timestamp {stat.timestamp}", file=sys.stderr)
            self.receiver_dict[stat.timestamp] = stat
        for stat in self.sender_statistics:
            if stat.timestamp in self.sender_dict:
                print(f"testlatency: duplicate sender timestamp {stat.timestamp}", file=sys.stderr)
            self.sender_dict[stat.timestamp] = stat
            
    def analyse(self, skipInitial : int = 0) -> AnalyserResults:
        self._gendicts()
        # We may want to ignore the first few point clouds, as they may be outliers
        if skipInitial > 0:
            self.receiver_statistics = self.receiver_statistics[skipInitial:]
            self.sender_statistics = self.sender_statistics[skipInitial:]
        count_total = len(self.sender_statistics)
        count_lost = 0
        for ts in self.sender_dict.keys():
            if ts not in self.receiver_dict:
                count_lost += 1
        latencies : list[float] = []
        for recv in self.receiver_statistics:
            if recv.timestamp not in self.sender_dict:
                print(f"testlatency: received frame {recv.timestamp} not found in sender statistics", file=sys.stderr)
                continue
            send = self.sender_dict[recv.timestamp]
            latency = recv.timestamp - send.timestamp
            latencies.append(latency)
        latency_min = min(latencies) if latencies else 0
        latency_max = max(latencies) if latencies else 0
        latency_avg = statistics.mean(latencies)
        latency_stddev = statistics.stdev(latencies)
        return AnalyserResults(count_total, count_lost, latency_min, latency_max, latency_avg, latency_stddev)
    
    def print(self, results: AnalyserResults):
        print(f"testlatency: count_total={results.count_total}, count_lost={results.count_lost}, latency_min={results.latency_min}, latency_max={results.latency_max}, latency_avg={results.latency_avg}, latency_stddev={results.latency_stddev}")