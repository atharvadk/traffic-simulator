# algorithms/fixed.py
from config import LANE_NAMES, PEDESTRIAN_TIME

class FixedCycleController:
    def __init__(self, green_time=20):
        self.green_time  = green_time
        self.phase_index = 0
        self.timer       = 0.0
        self.ped_timer   = 0.0
        self.ped_phase   = False
        self.ped_count   = 0
        self.phases      = [{'North'}, {'East'}, {'South'}, {'West'}]

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
            self.phase_index = (self.phase_index + 1) % len(self.phases)
            intersection.cycle_count += 1

            if self.phase_index % 2 == 0 and self.ped_count < 2:
                self.ped_phase = True
                self.ped_timer = PEDESTRIAN_TIME
                self.ped_count += 1
                intersection.current_green = set()
            else:
                if self.phase_index == 0:
                    self.ped_count = 0
                self._next_phase(intersection)

    def _next_phase(self, intersection):
        intersection.current_green = set(self.phases[self.phase_index])
        self.timer = self.green_time

    def start(self, intersection):
        intersection.current_green = set(self.phases[self.phase_index])
        self.timer = self.green_time

    def get_status(self):
        if self.ped_phase:
            return f"Pedestrian crossing   {self.ped_timer:.1f}s"
        lane = list(self.current_phase())[0]
        return f"Green: {lane}   {self.timer:.1f}s remaining"