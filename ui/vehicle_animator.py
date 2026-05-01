# ui/vehicle_animator.py
import math

# Entry points — where vehicle starts crossing (relative to cx, cy)
def get_entry_point(lane, cx, cy, lw):
    if lane == 'North-Left':
        return (cx - lw - lw // 2, cy - lw * 3)
    elif lane == 'North-Right':
        return (cx - lw // 2,      cy - lw * 3)
    elif lane == 'South-Left':
        return (cx + lw // 2,      cy + lw * 3)
    elif lane == 'South-Right':
        return (cx + lw + lw // 2, cy + lw * 3)
    elif lane == 'East-Left':
        return (cx + lw * 3,       cy - lw - lw // 2)
    elif lane == 'East-Right':
        return (cx + lw * 3,       cy - lw // 2)
    elif lane == 'West-Left':
        return (cx - lw * 3,       cy + lw // 2)
    elif lane == 'West-Right':
        return (cx - lw * 3,       cy + lw + lw // 2)
    return (cx, cy)

# Exit points — where vehicle ends crossing (exit lane center)
def get_exit_point(exit_arm, cx, cy, lw):
    if exit_arm == 'North':
        return (cx + lw + lw // 2, cy - lw * 4)
    elif exit_arm == 'South':
        return (cx - lw - lw // 2, cy + lw * 4)
    elif exit_arm == 'East':
        return (cx + lw * 4,       cy + lw + lw // 2)
    elif exit_arm == 'West':
        return (cx - lw * 4,       cy - lw - lw // 2)
    return (cx, cy)


class CrossingVehicle:
    def __init__(self, vehicle, start, end, color):
        self.vehicle  = vehicle
        self.start    = start
        self.end      = end
        self.color    = color
        self.progress = 0.0
        self.speed    = 0.5
        self.done     = False
        self.trail    = []

    def update(self, dt):
        self.progress += self.speed * dt
        if self.progress >= 1.0:
            self.progress = 1.0
            self.done     = True

        x = self.start[0] + (self.end[0] - self.start[0]) * self.progress
        y = self.start[1] + (self.end[1] - self.start[1]) * self.progress
        self.trail.append((x, y, 1.0 - self.progress))
        if len(self.trail) > 10:
            self.trail.pop(0)

    @property
    def pos(self):
        x = self.start[0] + (self.end[0] - self.start[0]) * self.progress
        y = self.start[1] + (self.end[1] - self.start[1]) * self.progress
        return (int(x), int(y))


class VehicleAnimator:
    def __init__(self):
        self.crossing = []

    def spawn(self, vehicle, cx, cy, lw, color):
        if not vehicle.exit_arm:
            return
        start = get_entry_point(vehicle.lane, cx, cy, lw)
        end   = get_exit_point(vehicle.exit_arm, cx, cy, lw)
        self.crossing.append(CrossingVehicle(vehicle, start, end, color))

    def update(self, dt):
        for cv in self.crossing:
            cv.update(dt)
        self.crossing = [cv for cv in self.crossing if not cv.done]

    def get_active(self):
        return self.crossing