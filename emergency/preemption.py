# emergency/preemption.py
from config import LANE_NAMES

class EmergencyHandler:
    def __init__(self):
        self.active            = False
        self.ev_lane           = None
        self.ev_timer          = 0.0
        self.corridor_duration = 20.0
        self.stolen_time       = {}
        self.flash_timer       = 0.0

    def trigger(self, lane, intersection):
        if self.active:
            return
        self.active   = True
        self.ev_lane  = lane
        self.ev_timer = self.corridor_duration
        self.flash_timer = 0.0
        self.stolen_time = {l: 0.0 for l in LANE_NAMES if l != lane}
        intersection.emergency_active = True
        intersection.emergency_lane   = lane

    def update(self, dt, intersection):
        if not self.active:
            return False

        self.flash_timer += dt
        self.ev_timer    -= dt

        # also check if EV vehicle is still in the queue
        ev_still_present = any(
            v.type == 'emergency'
            for v in intersection.queues.get(self.ev_lane, [])
        )

        # clear when timer runs out OR vehicle has left the queue
        if self.ev_timer <= 0 or not ev_still_present:
            self._clear(intersection)
            return True

        return False

    def _clear(self, intersection):
        self.active                   = False
        self.ev_lane                  = None
        self.ev_timer                 = 0.0
        self.flash_timer              = 0.0
        intersection.emergency_active = False
        intersection.emergency_lane   = None
        intersection.current_green    = set()

    def get_stolen_time(self):
        return self.stolen_time.copy()

    @property
    def flash_on(self):
        return int(self.flash_timer * 2) % 2 == 0

    def get_status(self):
        if not self.active:
            return None
        return f"EMERGENCY: {self.ev_lane} corridor   {self.ev_timer:.1f}s"