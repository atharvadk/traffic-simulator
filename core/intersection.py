# core/intersection.py
from config import LANE_NAMES, MAX_WAIT_CAP

class Intersection:
    def __init__(self):
        self.queues = {lane: [] for lane in LANE_NAMES}
        self.current_green  = set()
        self.phase_timer    = 0.0
        self.cycle_count    = 0
        self.starvation_timers = {lane: 0.0 for lane in LANE_NAMES}
        self.emergency_active  = False
        self.emergency_lane    = None

    def add_vehicle(self, vehicle):
        self.queues[vehicle.lane].append(vehicle)

    def clear_vehicle(self, lane):
        if self.queues[lane]:
            return self.queues[lane].pop(0)
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

    def get_state(self):
        return {
            lane: {
                'queue_length' : self.queue_length(lane),
                'pressure'     : self.total_pressure(lane),
                'is_green'     : self.is_green(lane),
                'starvation'   : self.starvation_timers[lane]
            }
            for lane in LANE_NAMES
        }