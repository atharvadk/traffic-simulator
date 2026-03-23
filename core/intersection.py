# core/intersection.py
from config import LANE_NAMES, MAX_WAIT_CAP

# how many seconds it takes each vehicle type to clear
CLEAR_TIMES = {
    'two_wheeler':  0.8,
    'four_wheeler': 1.2,
    'heavy':        2.5,
    'emergency':    0.3,
}

class Intersection:
    def __init__(self):
        self.queues            = {lane: [] for lane in LANE_NAMES}
        self.current_green     = set()
        self.phase_timer       = 0.0
        self.cycle_count       = 0
        self.starvation_timers = {lane: 0.0 for lane in LANE_NAMES}
        self.emergency_active  = False
        self.emergency_lane    = None
        self.clear_timers      = {lane: 0.0 for lane in LANE_NAMES}
        self.cleared_count     = 0
        self.total_wait        = 0.0
        self.wait_samples      = 0

    def add_vehicle(self, vehicle):
        self.queues[vehicle.lane].append(vehicle)

    def clear_vehicle(self, lane):
        if self.queues[lane]:
            v = self.queues[lane].pop(0)
            self.total_wait   += v.wait_time
            self.wait_samples += 1
            self.cleared_count += 1
            return v
        return None

    def queue_length(self, lane):
        return len(self.queues[lane])

    def total_pressure(self, lane):
        return sum(v.weight for v in self.queues[lane])

    def is_green(self, lane):
        return lane in self.current_green

    def update_starvation(self, dt):
        for lane in LANE_NAMES:
            if lane not in self.current_green:
                self.starvation_timers[lane] += dt
            else:
                self.starvation_timers[lane] = 0.0

    def is_starving(self, lane):
        return self.starvation_timers[lane] >= MAX_WAIT_CAP

    def update_clearing(self, dt):
        for lane in self.current_green:
            if not self.queues[lane]:
                continue
            self.clear_timers[lane] += dt
            next_vehicle = self.queues[lane][0]
            threshold    = CLEAR_TIMES.get(next_vehicle.type, 1.2)
            while self.clear_timers[lane] >= threshold and self.queues[lane]:
                self.clear_timers[lane] -= threshold
                self.clear_vehicle(lane)
                if self.queues[lane]:
                    threshold = CLEAR_TIMES.get(self.queues[lane][0].type, 1.2)

    @property
    def avg_wait_time(self):
        if self.wait_samples == 0:
            return 0.0
        return self.total_wait / self.wait_samples

    def get_state(self):
        return {
            lane: {
                'queue_length': self.queue_length(lane),
                'pressure':     self.total_pressure(lane),
                'is_green':     self.is_green(lane),
                'starvation':   self.starvation_timers[lane]
            }
            for lane in LANE_NAMES
        }