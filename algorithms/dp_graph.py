# algorithms/dp_graph.py
from itertools import combinations
from config import (LANE_NAMES, PEDESTRIAN_TIME, MIN_GREEN_TIME,
                    MAX_GREEN_TIME, MAX_WAIT_CAP, CONFLICT_GRAPH)

# precompute all valid independent sets once at import time
def _compute_independent_sets():
    valid = []
    for r in range(1, len(LANE_NAMES) + 1):
        for subset in combinations(LANE_NAMES, r):
            subset_set = set(subset)
            is_valid = all(
                subset_set.isdisjoint(CONFLICT_GRAPH[lane])
                for lane in subset
            )
            if is_valid:
                valid.append(subset_set)
    return valid

INDEPENDENT_SETS = _compute_independent_sets()

class DPController:
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

    def _starvation_bonus(self, lane, intersection):
        wait = intersection.starvation_timers[lane]
        # bonus kicks in after 60s, grows linearly up to MAX_WAIT_CAP
        return max(0.0, wait - 60) * 0.8

    def _lane_score(self, lane, intersection):
        pressure = intersection.total_pressure(lane)
        bonus    = self._starvation_bonus(lane, intersection)
        return pressure + bonus

    def _dp_best_lane(self, candidates, intersection):
        # starvation override first
        for lane in candidates:
            if intersection.starvation_timers[lane] >= MAX_WAIT_CAP:
                return lane

        # find best independent set that contains only lanes
        # from current candidates — score each valid subset
        best_score = -1
        best_lane  = candidates[0]

        for iset in INDEPENDENT_SETS:
            # only consider sets fully within current candidates
            if not iset.issubset(set(candidates)):
                continue
            score = sum(self._lane_score(l, intersection) for l in iset)
            if score > best_score:
                best_score = score
                # pick the single highest scoring lane from this set
                best_lane  = max(iset, key=lambda l: self._lane_score(l, intersection))

        return best_lane

    def _allocate_time(self, lane, intersection):
        lane_score   = self._lane_score(lane, intersection)
        total_score  = sum(self._lane_score(l, intersection) for l in LANE_NAMES)

        if total_score == 0:
            return MIN_GREEN_TIME

        ratio = lane_score / total_score
        time  = ratio * 80
        return max(MIN_GREEN_TIME, min(MAX_GREEN_TIME, time))

    def _start_next_phase(self, intersection):
        candidates        = self.groups[self.group]
        self.current_lane = self._dp_best_lane(candidates, intersection)
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
                self._start_next_phase(intersection)
            else:
                self.ped_phase = True
                self.ped_timer = PEDESTRIAN_TIME
                intersection.current_green = set()

    def get_status(self):
        if self.ped_phase:
            return f"Pedestrian crossing   {self.ped_timer:.1f}s"
        if self.current_lane:
            return f"Green: {self.current_lane}   {self.timer:.1f}s remaining"
        return "Initialising..."