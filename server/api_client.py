# server/api_client.py
import requests
import threading

SERVER_URL = 'http://127.0.0.1:5000'

class OptimizerClient:
    def __init__(self):
        self.connected    = False
        self.last_result  = None
        self.pending      = False
        self._check_connection()

    def _check_connection(self):
        try:
            r = requests.get(f'{SERVER_URL}/status', timeout=2)
            if r.status_code == 200:
                self.connected = True
                print("[Client] Connected to optimizer server.")
        except Exception:
            self.connected = False
            print("[Client] Optimizer server not reachable — running standalone.")

    def _build_payload(self, intersection, algo_name, group_index, phase_index):
        lanes_data = {}
        for lane in intersection.queues:
            lanes_data[lane] = {
                'queue':    intersection.queue_length(lane),
                'pressure': intersection.total_pressure(lane),
                'wait':     intersection.starvation_timers[lane]
            }
        return {
            'lanes':           lanes_data,
            'algorithm':       algo_name,
            'group_index':     group_index,
            'phase_index':     phase_index,
            'emergency_active': intersection.emergency_active,
            'emergency_lane':  intersection.emergency_lane
        }

    def request_decision(self, intersection, algo_name, group_index, phase_index, callback):
        if not self.connected:
            return

        payload = self._build_payload(intersection, algo_name, group_index, phase_index)

        # run in background thread so it never blocks pygame
        def _call():
            try:
                r = requests.post(
                    f'{SERVER_URL}/decide',
                    json=payload,
                    timeout=2
                )
                if r.status_code == 200:
                    result = r.json()
                    self.last_result = result
                    callback(result)
            except Exception as e:
                print(f"[Client] Request failed: {e}")

        threading.Thread(target=_call, daemon=True).start()