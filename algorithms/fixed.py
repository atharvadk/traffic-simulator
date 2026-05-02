# algorithms/fixed.py
from config import PEDESTRIAN_TIME, MIN_GREEN_TIME

class FixedCycleController:
    def __init__(self, green_time=20):
        self.green_time  = green_time
        self.timer       = 0.0
        self.ped_timer   = 0.0
        self.ped_phase   = False
        self.group_index = 0
        self.groups      = [
            ['North-Left', 'North-Right'],
            ['East-Left',  'East-Right'],
            ['South-Left', 'South-Right'],
            ['West-Left',  'West-Right'],
        ]

    def start(self, intersection):
        self.group_index = 0
        intersection.current_green = set(self.groups[0])
        self.timer = self.green_time
        intersection.cycle_count += 1

    def update(self, dt, intersection):
        if self.ped_phase:
            self.ped_timer -= dt
            intersection.current_green = set()
            if self.ped_timer <= 0:
                self.ped_phase   = False
                self.group_index = 0
                intersection.current_green = set(self.groups[0])
                self.timer = self.green_time
                intersection.cycle_count += 1
            return

        self.timer -= dt
        intersection.update_starvation(dt)

        if self.timer <= 0:
            self.group_index += 1
            if self.group_index < len(self.groups):
                # next group
                intersection.current_green = set(self.groups[self.group_index])
                self.timer = self.green_time
                intersection.cycle_count += 1
            else:
                # all groups done — pedestrian
                self.ped_phase = True
                self.ped_timer = PEDESTRIAN_TIME
                intersection.current_green = set()

    def get_status(self):
        if self.ped_phase:
            return f"Pedestrian   {self.ped_timer:.1f}s"
        if self.group_index < len(self.groups):
            arm = self.groups[self.group_index][0].replace('-Left','').replace('-Right','')
            return f"Green: {arm}   {self.timer:.1f}s  [FIXED]"
        return "Transitioning..."