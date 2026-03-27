# emergency/preemption.py
from config import LANE_NAMES, PEDESTRIAN_TIME

class EmergencyHandler:
    def __init__(self):
        self.active       = False
        self.ev_lane      = None
        self.ev_timer     = 0.0
        self.corridor_duration = 20.0
        self.stolen_time  = {}
        self.flash_timer  = 0.0

    def trigger(self, lane, intersection):
        if self.active:
            return  # already handling one

        self.active   = True
        self.ev_lane  = lane
        self.ev_timer = self.corridor_duration
        self.flash_timer = 0.0

        # record how much time was stolen from other lanes
        self.stolen_time = {
            l: 0.0 for l in LANE_NAMES if l != lane
        }

        # mark on intersection
        intersection.emergency_active = True
        intersection.emergency_lane   = lane
        intersection.current_green    = {lane}

    def update(self, dt, intersection):
        if not self.active:
            return False

        self.ev_timer    -= dt
        self.flash_timer += dt

        # keep green corridor open
        intersection.current_green = {self.ev_lane}

        if self.ev_timer <= 0:
            self._clear(intersection)
            return True  # signals controller to resume

        return False

    def _clear(self, intersection):
        self.active                   = False
        intersection.emergency_active = False
        intersection.emergency_lane   = None
        intersection.current_green    = set()

    def get_stolen_time(self):
        return self.stolen_time.copy()

    @property
    def flash_on(self):
        # flashes every 0.5s for visual effect
        return int(self.flash_timer * 2) % 2 == 0

    def get_status(self):
        if not self.active:
            return None
        return f"EMERGENCY: {self.ev_lane} corridor   {self.ev_timer:.1f}s"