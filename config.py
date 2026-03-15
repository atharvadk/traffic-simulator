# config.py

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

VEHICLE_WEIGHTS = {
    'two_wheeler':  0.5,
    'four_wheeler': 1.0,
    'heavy':        3.0,
    'emergency':    999
}

LANE_NAMES = ['North', 'South', 'East', 'West']

CONFLICT_GRAPH = {
    'North': {'East', 'West'},
    'South': {'East', 'West'},
    'East':  {'North', 'South'},
    'West':  {'North', 'South'}
}

COMPATIBLE_PAIRS = [
    {'North', 'South'},
    {'East', 'West'}
]

MAX_WAIT_CAP    = 90
MIN_GREEN_TIME  = 10
MAX_GREEN_TIME  = 60
PEDESTRIAN_TIME = 15
ADAPTIVE_THRESHOLD = 5