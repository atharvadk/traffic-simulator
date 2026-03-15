# core/vehicle.py
import time
from config import VEHICLE_WEIGHTS

class Vehicle:
    def __init__(self, vehicle_type, lane):
        self.type         = vehicle_type
        self.weight       = VEHICLE_WEIGHTS[vehicle_type]
        self.lane         = lane
        self.arrival_time = time.time()

    @property
    def wait_time(self):
        return time.time() - self.arrival_time

    def __repr__(self):
        return f"Vehicle({self.type}, lane={self.lane}, wait={self.wait_time:.1f}s)"