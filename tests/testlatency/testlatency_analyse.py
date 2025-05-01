import sys
from collections import namedtuple
import statistics
from testlatency_receiver import ReceiverStatistics
from testlatency_sender import SenderStatistics

AnalyserResults = namedtuple("AnalyserResults", ["count_total", "count_lost_initial", "count_lost_running", "latency_ignored_count", "latency_min", "latency_max", "latency_avg", "latency_stddev"])
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
            
    def analyse(self, ignore_initial_latencies : bool = False) -> AnalyserResults:
        self._gendicts()
        
        count_total = len(self.sender_statistics)
        count_lost_initial = 0
        count_lost_running = 0
        saw_initial_frame = False
        for ts in self.sender_dict.keys():
            if ts in self.receiver_dict:
                saw_initial_frame = True
            else:
                if saw_initial_frame:
                    count_lost_running += 1
                else:
                    count_lost_initial += 1
        latencies : list[float] = []
        for recv in self.receiver_statistics:
            if recv.timestamp not in self.sender_dict:
                print(f"testlatency: received frame {recv.timestamp} not found in sender statistics", file=sys.stderr)
                continue
            send = self.sender_dict[recv.timestamp]
            latency = recv.receiver_wallclock - send.sender_wallclock
            latencies.append(latency)
        if ignore_initial_latencies:
            full_average = statistics.mean(latencies) if latencies else 0
            for first_below_average in range(1, len(latencies)):
                if latencies[first_below_average] < full_average:
                    break
            latencies = latencies[first_below_average:]
        else:
            first_below_average = 0
        latency_min = min(latencies) if latencies else 0
        latency_max = max(latencies) if latencies else 0
        latency_avg = statistics.mean(latencies) if latencies else 0
        latency_stddev = statistics.stdev(latencies) if len(latencies) > 1 else 0
        return AnalyserResults(count_total, count_lost_initial, count_lost_running, first_below_average, latency_min, latency_max, latency_avg, latency_stddev)
    
    def print(self, results: AnalyserResults):
        print(f"testlatency: count_total={results.count_total}, count_lost_initial={results.count_lost_initial}, count_lost_running={results.count_lost_running}, latency_ignored_count={results.latency_ignored_count}, latency_min={results.latency_min:.3f}, latency_max={results.latency_max:.3f}, latency_avg={results.latency_avg:.3f}, latency_stddev={results.latency_stddev:.3f}")