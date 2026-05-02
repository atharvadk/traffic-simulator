# algorithms/dp_graph.py
from itertools import permutations
from config import (LANE_NAMES, PEDESTRIAN_TIME, MIN_GREEN_TIME,
                    MAX_GREEN_TIME, MAX_WAIT_CAP,
                    LOW_PRESSURE_THRESHOLD, YELLOW_DURATION)

class DPController:
    def __init__(self):
        self.timer         = 0.0
        self.ped_timer     = 0.0
        self.ped_phase     = False
        self.yellow_phase  = False
        self.yellow_timer  = 0.0
        self.current_group = None
        self.cycle_order   = []
        self.order_index   = 0
        self.groups        = [
            ['North-Left', 'North-Right'],
            ['East-Left',  'East-Right'],
            ['South-Left', 'South-Right'],
            ['West-Left',  'West-Right'],
        ]

    def _group_pressure(self, group, intersection):
        return sum(intersection.total_pressure(l) for l in group)

    def _starvation_score(self, group, intersection):
        bonus = 0.0
        for l in group:
            wait = intersection.starvation_timers[l]
            if wait >= MAX_WAIT_CAP:
                bonus += 9999
            elif wait > 60:
                bonus += (wait - 60) * 0.8
        return bonus

    def _group_score(self, group, intersection):
        return (self._group_pressure(group, intersection) +
                self._starvation_score(group, intersection))

    def _dp_optimal_order(self, intersection):
        scores    = [self._group_score(g, intersection) for g in self.groups]
        best_val  = -1
        best_order = list(range(len(self.groups)))
        for perm in permutations(range(len(self.groups))):
            val = sum(scores[perm[pos]] / (pos + 1)
                      for pos in range(len(perm)))
            if val > best_val:
                best_val   = val
                best_order = list(perm)
        return [self.groups[i] for i in best_order]

    def _allocate_time(self, group, intersection):
        gs = self._group_score(group, intersection)
        ts = sum(self._group_score(g, intersection) for g in self.groups)
        if ts == 0:
            return MIN_GREEN_TIME
        return round(max(MIN_GREEN_TIME, min(MAX_GREEN_TIME, (gs / ts) * 80)), 1)

    def _trigger_yellow(self, intersection):
        self.yellow_phase = True
        self.yellow_timer = YELLOW_DURATION
        intersection.current_green = set()

    def _start_cycle(self, intersection):
        self.yellow_phase = False
        self.cycle_order  = self._dp_optimal_order(intersection)
        self.order_index  = 0
        self._serve_current(intersection)

    def _serve_current(self, intersection):
        self.yellow_phase = False
        if self.order_index >= len(self.cycle_order):
            self.ped_phase = True
            self.ped_timer = PEDESTRIAN_TIME
            intersection.current_green = set()
            return
        self.current_group = self.cycle_order[self.order_index]
        intersection.current_green = set(self.current_group)
        self.timer = self._allocate_time(self.current_group, intersection)
        intersection.cycle_count += 1

    def start(self, intersection):
        self._start_cycle(intersection)

    def update(self, dt, intersection):
        if self.ped_phase:
            self.ped_timer -= dt
            intersection.current_green = set()
            if self.ped_timer <= 0:
                self.ped_phase = False
                self._start_cycle(intersection)
            return

        if self.yellow_phase:
            self.yellow_timer -= dt
            if self.yellow_timer <= 0:
                self.order_index += 1
                self._serve_current(intersection)
            return

        self.timer -= dt
        intersection.update_starvation(dt)

        # early cut
        if self.current_group:
            pressure = self._group_pressure(self.current_group, intersection)
            if pressure <= LOW_PRESSURE_THRESHOLD and self.timer > 0:
                self._trigger_yellow(intersection)
                return

        if self.timer <= 0:
            self._trigger_yellow(intersection)

    def emergency_interrupt(self, lane, intersection):
        for i, group in enumerate(self.groups):
            if lane in group:
                self.current_group = group
                self.cycle_order   = [g for g in self.cycle_order if g != group]
                self.order_index   = len(self.cycle_order)
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
        self.yellow_phase = False
        intersection.current_green = set(self.current_group)
        self.timer = result['green_time']
        intersection.cycle_count += 1

    def get_status(self):
        if self.ped_phase:
            return f"Pedestrian   {self.ped_timer:.1f}s"
        if self.yellow_phase:
            arm = self.current_group[0].replace('-Left','').replace('-Right','')
            return f"Yellow: {arm}   {self.yellow_timer:.1f}s  [DP]"
        if self.current_group:
            arm = self.current_group[0].replace('-Left','').replace('-Right','')
            pos = self.order_index + 1
            return f"Green: {arm}   {self.timer:.1f}s  [DP #{pos}]"
        return "Initialising..."