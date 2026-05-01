# core/vehicle.py
import time
from config import VEHICLE_WEIGHTS, EXIT_MAP

class Vehicle:
    def __init__(self, vehicle_type, lane, direction=None):
        self.type         = vehicle_type
        self.weight       = VEHICLE_WEIGHTS[vehicle_type]
        self.lane         = lane
        self.direction    = direction
        self.arrival_time = time.time()
        self.exit_arm     = EXIT_MAP.get((lane, direction), None)

    @property
    def wait_time(self):
        return time.time() - self.arrival_time

    def __repr__(self):
        return (f"Vehicle({self.type}, lane={self.lane}, "
                f"dir={self.direction}, exit={self.exit_arm}, "
                f"wait={self.wait_time:.1f}s)")