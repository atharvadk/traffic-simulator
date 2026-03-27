# algorithms/greedy.py
from config import LANE_NAMES, PEDESTRIAN_TIME, MIN_GREEN_TIME, MAX_GREEN_TIME, MAX_WAIT_CAP

class GreedyController:
    def __init__(self):
        self.timer          = 0.0
        self.ped_timer      = 0.0
        self.ped_phase      = False
        self.current_lane   = None
        self.phase_in_group = 0
        self.group          = 0
        self.groups         = [
            ['North', 'East'],
            ['South', 'West']
        ]

    def _pick_lane(self, candidates, intersection):
        # starvation check first — only among current group
        for lane in candidates:
            if intersection.starvation_timers[lane] >= MAX_WAIT_CAP:
                return lane

        # pick highest pressure lane in this group
        return max(
            candidates,
            key=lambda lane: intersection.total_pressure(lane)
        )

    def _allocate_time(self, lane, intersection):
        lane_pressure  = intersection.total_pressure(lane)
        total_pressure = sum(intersection.total_pressure(l) for l in LANE_NAMES)

        if total_pressure == 0:
            return MIN_GREEN_TIME

        ratio = lane_pressure / total_pressure
        time  = ratio * 80
        return max(MIN_GREEN_TIME, min(MAX_GREEN_TIME, time))

    def _start_next_phase(self, intersection):
        candidates        = self.groups[self.group]
        self.current_lane = self._pick_lane(candidates, intersection)
        intersection.current_green = {self.current_lane}
        self.timer = self._allocate_time(self.current_lane, intersection)
        intersection.cycle_count += 1

    def start(self, intersection):
        self.group          = 0
        self.phase_in_group = 0
        self._start_next_phase(intersection)

    def update(self, dt, intersection):
        if self.ped_phase:
            self.ped_timer -= dt
            intersection.current_green = set()
            if self.ped_timer <= 0:
                self.ped_phase      = False
                self.group          = (self.group + 1) % 2
                self.phase_in_group = 0
                self._start_next_phase(intersection)
            return

        self.timer -= dt
        intersection.update_starvation(dt)

        if self.timer <= 0:
            self.phase_in_group += 1
            if self.phase_in_group < 2:
                # first lane in group done, move to second
                self._start_next_phase(intersection)
            else:
                # both lanes done, pedestrian phase
                self.ped_phase = True
                self.ped_timer = PEDESTRIAN_TIME
                intersection.current_green = set()

    def get_status(self):
        if self.ped_phase:
            return f"Pedestrian crossing   {self.ped_timer:.1f}s"
        if self.current_lane:
            return f"Green: {self.current_lane}   {self.timer:.1f}s remaining"
        return "Initialising..."