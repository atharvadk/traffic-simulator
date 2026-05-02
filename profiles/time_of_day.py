# profiles/time_of_day.py
import random
from core.vehicle import Vehicle
from config import LANE_NAMES

PROFILES = {
    'morning': {
        'weights': {
            'two_wheeler':  0.51,
            'four_wheeler': 0.41,
            'heavy':        0.08,
        },
        'arrival_rate': 0.3,
        'cycle_budget': 120
    },
    'afternoon': {
        'weights': {
            'two_wheeler':  0.31,
            'four_wheeler': 0.46,
            'heavy':        0.23,
        },
        'arrival_rate': 0.15,
        'cycle_budget': 100
    },
    'evening': {
        'weights': {
            'two_wheeler':  0.26,
            'four_wheeler': 0.61,
            'heavy':        0.13,
        },
        'arrival_rate': 0.25,
        'cycle_budget': 120
    },
    'night': {
        'weights': {
            'two_wheeler':  0.17,
            'four_wheeler': 0.21,
            'heavy':        0.62,
        },
        'arrival_rate': 0.08,
        'cycle_budget': 60
    }
}

LANE_DIRECTION_OPTIONS = {
    'North-Left':  ['left'],
    'North-Right': ['straight', 'right'],
    'South-Left':  ['left'],
    'South-Right': ['straight', 'right'],
    'East-Left':   ['left'],
    'East-Right':  ['straight', 'right'],
    'West-Left':   ['left'],
    'West-Right':  ['straight', 'right'],
}

def pick_vehicle_type(profile_name):
    profile    = PROFILES[profile_name]
    r          = random.random()
    cumulative = 0.0
    for vtype, prob in profile['weights'].items():
        cumulative += prob
        if r <= cumulative:
            return vtype
    return 'four_wheeler'

def pick_direction(lane):
    options = LANE_DIRECTION_OPTIONS.get(lane, ['straight'])
    return random.choice(options)

def spawn_vehicle(lane, profile_name):
    vtype     = pick_vehicle_type(profile_name)
    direction = pick_direction(lane)
    return Vehicle(vtype, lane, direction)


class VehicleSpawner:
    def __init__(self, profile_name='morning'):
        self.profile_name = profile_name
        self.timers       = {lane: 0.0 for lane in LANE_NAMES}

    def set_profile(self, profile_name):
        self.profile_name = profile_name
        self.timers       = {lane: 0.0 for lane in LANE_NAMES}

    def update(self, dt, intersection):
        profile  = PROFILES[self.profile_name]
        rate     = profile['arrival_rate']
        interval = 1.0 / rate

        for lane in LANE_NAMES:
            self.timers[lane] += dt
            if self.timers[lane] >= interval:
                self.timers[lane] = 0.0
                if random.random() < 0.75:
                    vehicle = spawn_vehicle(lane, self.profile_name)
                    intersection.add_vehicle(vehicle)

    @property
    def arrival_rate(self):
        return PROFILES[self.profile_name]['arrival_rate']