# algorithms/fixed.py
from config import LANE_NAMES, MIN_GREEN_TIME, MAX_GREEN_TIME, PEDESTRIAN_TIME, COMPATIBLE_PAIRS

class FixedCycleController:
    def __init__(self, green_time=20):
        self.green_time   = green_time
        self.phase_index  = 0
        self.timer        = 0.0
        self.ped_timer    = 0.0
        self.ped_phase    = False
        self.phases       = list(COMPATIBLE_PAIRS)

    def current_phase(self):
        return self.phases[self.phase_index]

    def update(self, dt, intersection):
        if self.ped_phase:
            self.ped_timer -= dt
            intersection.current_green = set()
            if self.ped_timer <= 0:
                self.ped_phase = False
                self._next_phase(intersection)
            return

        self.timer -= dt
        intersection.update_starvation(dt)

        if self.timer <= 0:
            self.ped_phase = True
            self.ped_timer = PEDESTRIAN_TIME
            intersection.current_green = set()

    def _next_phase(self, intersection):
        self.phase_index = (self.phase_index + 1) % len(self.phases)
        intersection.current_green = set(self.phases[self.phase_index])
        intersection.cycle_count  += 1
        self.timer = self.green_time

    def start(self, intersection):
        intersection.current_green = set(self.phases[self.phase_index])
        self.timer = self.green_time

    def get_status(self):
        if self.ped_phase:
            return f"Pedestrian crossing  {self.ped_timer:.1f}s"
        phase = self.current_phase()
        names = ' + '.join(sorted(phase))
        return f"Green: {names}   {self.timer:.1f}s remaining"