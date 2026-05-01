# profiles/time_of_day.py
import random
from core.vehicle import Vehicle
from config import LANE_NAMES

PROFILES = {
    'morning': {
        'weights': {
            'two_wheeler':  0.50,
            'four_wheeler': 0.40,
            'heavy':        0.08,
            'emergency':    0.02,
        },
        'arrival_rate': 0.3,
        'cycle_budget': 120
    },
    'afternoon': {
        'weights': {
            'two_wheeler':  0.30,
            'four_wheeler': 0.45,
            'heavy':        0.23,
            'emergency':    0.02,
        },
        'arrival_rate': 0.15,
        'cycle_budget': 100
    },
    'evening': {
        'weights': {
            'two_wheeler':  0.25,
            'four_wheeler': 0.60,
            'heavy':        0.13,
            'emergency':    0.02,
        },
        'arrival_rate': 0.25,
        'cycle_budget': 120
    },
    'night': {
        'weights': {
            'two_wheeler':  0.15,
            'four_wheeler': 0.20,
            'heavy':        0.63,
            'emergency':    0.02,
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