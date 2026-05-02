# algorithms/greedy.py
from config import (LANE_NAMES, PEDESTRIAN_TIME, MIN_GREEN_TIME,
                    MAX_GREEN_TIME, MAX_WAIT_CAP,
                    LOW_PRESSURE_THRESHOLD, YELLOW_DURATION)

class GreedyController:
    def __init__(self):
        self.timer         = 0.0
        self.ped_timer     = 0.0
        self.ped_phase     = False
        self.yellow_phase  = False
        self.yellow_timer  = 0.0
        self.current_group = None
        self.served        = []
        self.groups        = [
            ['North-Left', 'North-Right'],
            ['East-Left',  'East-Right'],
            ['South-Left', 'South-Right'],
            ['West-Left',  'West-Right'],
        ]

    def _group_pressure(self, group, intersection):
        return sum(intersection.total_pressure(l) for l in group)

    def _starvation_override(self, intersection):
        for group in self.groups:
            if group in self.served:
                continue
            if any(intersection.starvation_timers[l] >= MAX_WAIT_CAP
                   for l in group):
                return group
        return None

    def _pick_next_group(self, intersection):
        override = self._starvation_override(intersection)
        if override:
            return override
        unserved = [g for g in self.groups if g not in self.served]
        if not unserved:
            return None
        return max(unserved,
                   key=lambda g: self._group_pressure(g, intersection))

    def _allocate_time(self, group, intersection):
        gp = self._group_pressure(group, intersection)
        tp = sum(intersection.total_pressure(l) for l in LANE_NAMES)
        if tp == 0:
            return MIN_GREEN_TIME
        return round(max(MIN_GREEN_TIME, min(MAX_GREEN_TIME, (gp / tp) * 80)), 1)

    def _trigger_yellow(self, intersection):
        """Start yellow warning phase."""
        self.yellow_phase = True
        self.yellow_timer = YELLOW_DURATION
        intersection.current_green = set()   # renderer reads yellow_phase

    def _start_next(self, intersection):
        self.yellow_phase = False
        group = self._pick_next_group(intersection)
        if group is None:
            self.ped_phase = True
            self.ped_timer = PEDESTRIAN_TIME
            intersection.current_green = set()
            self.served = []
            return
        self.current_group = group
        self.served.append(group)
        intersection.current_green = set(group)
        self.timer = self._allocate_time(group, intersection)
        intersection.cycle_count += 1

    def start(self, intersection):
        self.served = []
        self._start_next(intersection)

    def update(self, dt, intersection):
        # pedestrian phase
        if self.ped_phase:
            self.ped_timer -= dt
            intersection.current_green = set()
            if self.ped_timer <= 0:
                self.ped_phase = False
                self.served    = []
                self._start_next(intersection)
            return

        # yellow warning phase
        if self.yellow_phase:
            self.yellow_timer -= dt
            if self.yellow_timer <= 0:
                self._start_next(intersection)
            return

        self.timer -= dt
        intersection.update_starvation(dt)

        # early cut — pressure dropped below threshold
        if self.current_group:
            pressure = self._group_pressure(self.current_group, intersection)
            if pressure <= LOW_PRESSURE_THRESHOLD and self.timer > 0:
                self._trigger_yellow(intersection)
                return

        if self.timer <= 0:
            self._trigger_yellow(intersection)

    def emergency_interrupt(self, lane, intersection):
        for group in self.groups:
            if lane in group:
                self.current_group = group
                self.served        = [group]
                self.yellow_phase  = False
                intersection.current_green = set(group)
                self.timer = 20.0
                return

    def apply_server_decision(self, result, intersection):
        lane = result['next_lane']
        for group in self.groups:
            if lane in group:
                self.current_group = group
                break
        self.served.append(self.current_group)
        self.yellow_phase = False
        intersection.current_green = set(self.current_group)
        self.timer = result['green_time']
        intersection.cycle_count += 1

    def get_status(self):
        if self.ped_phase:
            return f"Pedestrian   {self.ped_timer:.1f}s"
        if self.yellow_phase:
            arm = self.current_group[0].replace('-Left','').replace('-Right','')
            return f"Yellow: {arm}   {self.yellow_timer:.1f}s  [GREEDY]"
        if self.current_group:
            arm = self.current_group[0].replace('-Left','').replace('-Right','')
            return f"Green: {arm}   {self.timer:.1f}s  [GREEDY]"
        return "Initialising..."