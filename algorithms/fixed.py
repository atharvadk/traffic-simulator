# algorithms/fixed.py
from config import PEDESTRIAN_TIME

class FixedCycleController:
    def __init__(self, green_time=20):
        self.green_time     = green_time
        self.timer          = 0.0
        self.ped_timer      = 0.0
        self.ped_phase      = False
        self.group          = 0
        self.phase_in_group = 0
        self.groups         = [
            ['North-Left', 'North-Right', 'East-Left', 'East-Right'],
            ['South-Left', 'South-Right', 'West-Left', 'West-Right'],
        ]

    def _start_next_phase(self, intersection):
        lane = self.groups[self.group][self.phase_in_group]
        intersection.current_green = {lane}
        self.timer = self.green_time
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
            if self.phase_in_group < len(self.groups[self.group]):
                self._start_next_phase(intersection)
            else:
                self.ped_phase      = True
                self.ped_timer      = PEDESTRIAN_TIME
                intersection.current_green = set()

    def get_status(self):
        if self.ped_phase:
            return f"Pedestrian   {self.ped_timer:.1f}s"
        group = self.groups[self.group]
        if self.phase_in_group < len(group):
            return f"Green: {group[self.phase_in_group]}   {self.timer:.1f}s"
        return "Transitioning..."