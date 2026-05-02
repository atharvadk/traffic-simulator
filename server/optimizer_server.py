# server/optimizer_server.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, request, jsonify
from config import LANE_NAMES, MIN_GREEN_TIME, MAX_GREEN_TIME, MAX_WAIT_CAP, VEHICLE_WEIGHTS, CONFLICT_GRAPH

app = Flask(__name__)

# ── helpers ────────────────────────────────────────────────────────────

def pressure_score(lane_data):
    return lane_data.get('pressure', 0.0)

def starvation_bonus(lane_data):
    wait = lane_data.get('wait', 0.0)
    return max(0.0, wait - 60) * 0.8

def allocate_time(lane, lanes_data):
    score       = pressure_score(lanes_data[lane]) + starvation_bonus(lanes_data[lane])
    total_score = sum(
        pressure_score(lanes_data[l]) + starvation_bonus(lanes_data[l])
        for l in lanes_data
    )
    if total_score == 0:
        return MIN_GREEN_TIME
    ratio = score / total_score
    return round(max(MIN_GREEN_TIME, min(MAX_GREEN_TIME, ratio * 80)), 2)

GROUPS = [
    ['North-Left', 'North-Right', 'East-Left', 'East-Right'],
    ['South-Left', 'South-Right', 'West-Left', 'West-Right'],
]

# ── fixed ──────────────────────────────────────────────────────────────

def fixed_decision(data):
    group_index = data.get('group_index', 0)
    phase_index = data.get('phase_index', 0)
    group       = GROUPS[group_index]
    lane        = group[phase_index % len(group)]
    return {
        'next_lane':  lane,
        'green_time': 20,
        'reason':     f'fixed cycle — group {group_index} phase {phase_index}'
    }

# ── greedy ─────────────────────────────────────────────────────────────

def greedy_decision(data):
    lanes_data  = data['lanes']
    group_index = data.get('group_index', 0)
    candidates  = GROUPS[group_index]

    # starvation override
    for lane in candidates:
        if lanes_data[lane].get('wait', 0) >= MAX_WAIT_CAP:
            return {
                'next_lane':  lane,
                'green_time': allocate_time(lane, lanes_data),
                'reason':     f'starvation override — {lane} waited too long'
            }

    # pick highest pressure
    best = max(candidates, key=lambda l: pressure_score(lanes_data[l]))
    return {
        'next_lane':  best,
        'green_time': allocate_time(best, lanes_data),
        'reason':     f'greedy — highest pressure in group {group_index}'
    }

# ── dp ─────────────────────────────────────────────────────────────────

# CONFLICT_GRAPH = {
#     'North-Left':  {'East-Left', 'East-Right', 'West-Left', 'West-Right'},
#     'North-Right': {'East-Left', 'East-Right', 'West-Left', 'West-Right'},
#     'South-Left':  {'East-Left', 'East-Right', 'West-Left', 'West-Right'},
#     'South-Right': {'East-Left', 'East-Right', 'West-Left', 'West-Right'},
#     'East-Left':   {'North-Left', 'North-Right', 'South-Left', 'South-Right'},
#     'East-Right':  {'North-Left', 'North-Right', 'South-Left', 'South-Right'},
#     'West-Left':   {'North-Left', 'North-Right', 'South-Left', 'South-Right'},
#     'West-Right':  {'North-Left', 'North-Right', 'South-Left', 'South-Right'},
# }

from itertools import combinations

def compute_independent_sets():
    valid = []
    for r in range(1, len(LANE_NAMES) + 1):
        for subset in combinations(LANE_NAMES, r):
            s = set(subset)
            if all(s.isdisjoint(CONFLICT_GRAPH[l]) for l in subset):
                valid.append(s)
    return valid

INDEPENDENT_SETS = compute_independent_sets()

def dp_decision(data):
    lanes_data  = data['lanes']
    group_index = data.get('group_index', 0)
    candidates  = GROUPS[group_index]

    # starvation override
    for lane in candidates:
        if lanes_data[lane].get('wait', 0) >= MAX_WAIT_CAP:
            return {
                'next_lane':  lane,
                'green_time': allocate_time(lane, lanes_data),
                'reason':     f'starvation override — {lane} waited too long'
            }

    # score each valid independent set within candidates
    best_score = -1
    best_lane  = candidates[0]

    for iset in INDEPENDENT_SETS:
        if not iset.issubset(set(candidates)):
            continue
        score = sum(
            pressure_score(lanes_data[l]) + starvation_bonus(lanes_data[l])
            for l in iset
        )
        if score > best_score:
            best_score = score
            best_lane  = max(iset, key=lambda l: pressure_score(lanes_data[l]) + starvation_bonus(lanes_data[l]))

    return {
        'next_lane':  best_lane,
        'green_time': allocate_time(best_lane, lanes_data),
        'reason':     f'dp graph — best weighted independent set in group {group_index}'
    }

# ── emergency ──────────────────────────────────────────────────────────

def emergency_decision(data):
    lane = data.get('emergency_lane')
    return {
        'next_lane':  lane,
        'green_time': 20,
        'reason':     f'emergency corridor — {lane} lane cleared'
    }

# ── endpoint ───────────────────────────────────────────────────────────

@app.route('/decide', methods=['POST'])
def decide():
    data      = request.get_json()
    algorithm = data.get('algorithm', 'fixed')

    # emergency takes priority over everything
    if data.get('emergency_active') and data.get('emergency_lane'):
        result = emergency_decision(data)
    elif algorithm == 'greedy':
        result = greedy_decision(data)
    elif algorithm == 'dp':
        result = dp_decision(data)
    else:
        result = fixed_decision(data)

    return jsonify(result)

@app.route('/status', methods=['GET'])
def status():
    return jsonify({'status': 'online', 'algorithms': ['fixed', 'greedy', 'dp']})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)