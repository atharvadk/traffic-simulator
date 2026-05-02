# config.py

SCREEN_WIDTH  = 1440
SCREEN_HEIGHT = 900
LOW_PRESSURE_THRESHOLD = 1.0   # if group pressure drops below this, cut green early
YELLOW_DURATION        = 2.0   # seconds of yellow warning before red

VEHICLE_WEIGHTS = {
    'two_wheeler':  0.5,
    'four_wheeler': 1.0,
    'heavy':        3.0,
    'emergency':    999
}

# all incoming lanes (exit lanes are display only, not queues)
LANE_NAMES = [
    'North-Left', 'North-Right',
    'South-Left', 'South-Right',
    'East-Left',  'East-Right',
    'West-Left',  'West-Right',
]

# arms
ARMS = ['North', 'South', 'East', 'West']

# incoming lanes per arm
ARM_LANES = {
    'North': ['North-Left', 'North-Right'],
    'South': ['South-Left', 'South-Right'],
    'East':  ['East-Left',  'East-Right'],
    'West':  ['West-Left',  'West-Right'],
}

# direction each lane is dedicated to
LANE_DIRECTIONS = {
    'North-Left':  'left',
    'North-Right': 'straight',
    'South-Left':  'left',
    'South-Right': 'straight',
    'East-Left':   'left',
    'East-Right':  'straight',
    'West-Left':   'left',
    'West-Right':  'straight',
}

# exit map — (lane, direction) → exit arm
EXIT_MAP = {
    ('North-Left',  'left'):     'West',
    ('North-Right', 'straight'): 'South',
    ('North-Right', 'right'):    'East',
    ('South-Left',  'left'):     'East',
    ('South-Right', 'straight'): 'North',
    ('South-Right', 'right'):    'West',
    ('East-Left',   'left'):     'North',
    ('East-Right',  'straight'): 'West',
    ('East-Right',  'right'):    'South',
    ('West-Left',   'left'):     'South',
    ('West-Right',  'straight'): 'East',
    ('West-Right',  'right'):    'North',
}

# conflict graph — lanes that cannot be green simultaneously
CONFLICT_GRAPH = {
    'North-Left':  {'East-Left', 'East-Right', 'West-Left', 'West-Right'},
    'North-Right': {'East-Left', 'East-Right', 'West-Left', 'West-Right'},
    'South-Left':  {'East-Left', 'East-Right', 'West-Left', 'West-Right'},
    'South-Right': {'East-Left', 'East-Right', 'West-Left', 'West-Right'},
    'East-Left':   {'North-Left', 'North-Right', 'South-Left', 'South-Right'},
    'East-Right':  {'North-Left', 'North-Right', 'South-Left', 'South-Right'},
    'West-Left':   {'North-Left', 'North-Right', 'South-Left', 'South-Right'},
    'West-Right':  {'North-Left', 'North-Right', 'South-Left', 'South-Right'},
}

COMPATIBLE_PAIRS = [
    {'North-Left', 'North-Right', 'South-Left', 'South-Right'},
    {'East-Left',  'East-Right',  'West-Left',  'West-Right'},
]

MAX_WAIT_CAP       = 90
MIN_GREEN_TIME     = 10
MAX_GREEN_TIME     = 60
PEDESTRIAN_TIME    = 15
ADAPTIVE_THRESHOLD = 5

# lane width for rendering — each arm has 3 visual lanes (left, right, exit)
LANE_WIDTH = 36