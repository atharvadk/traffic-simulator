# algorithms/greedy.py
from config import (
    LANE_NAMES, PEDESTRIAN_TIME,
    MIN_GREEN_TIME, MAX_GREEN_TIME, MAX_WAIT_CAP, ADAPTIVE_THRESHOLD
)


class GreedyCycleController:
    """
    Adaptive greedy controller.

    Follows the same phase skeleton as FixedCycleController:
        phase 0 – North
        phase 1 – East
        [pedestrian crossing]
        phase 2 – South
        phase 3 – West
        [pedestrian crossing]
        … repeat …

    At every phase transition the green time for the *next* lane is chosen
    proportionally to its weighted pressure, clamped to [MIN_GREEN_TIME,
    MAX_GREEN_TIME].  If any non-green lane has been starving for ≥ MAX_WAIT_CAP
    seconds it is promoted immediately, skipping the normal cycle order for one
    phase, then the normal sequence resumes from where it was interrupted.
    """

    def __init__(self):
        self.phase_index  = 0                  # 0-3, index into self.phases
        self.timer        = 0.0                # seconds remaining in current green
        self.ped_timer    = 0.0
        self.ped_phase    = False
        self.ped_count    = 0                  # pedestrian phases fired this cycle
        self.phases       = ['North', 'East', 'South', 'West']

        # starvation-override state
        self._override_active = False          # currently serving a starved lane
        self._override_lane   = None
        self._resume_index    = 0              # phase_index to return to after override

        self._last_status = ""

    # ── public interface ────────────────────────────────────────────────

    def current_phase(self):
        return {self.phases[self.phase_index]}

    def start(self, intersection):
        """Call once before the main loop begins."""
        lane = self.phases[self.phase_index]
        intersection.current_green = {lane}
        self.timer = self._compute_green(lane, intersection)
        self._last_status = f"Green: {lane}   {self.timer:.1f}s"

    def update(self, dt, intersection):
        # ── pedestrian phase ──────────────────────────────────────────
        if self.ped_phase:
            self.ped_timer -= dt
            intersection.current_green = set()
            if self.ped_timer <= 0:
                self.ped_phase = False
                self._start_next_phase(intersection)
            return

        self.timer -= dt
        intersection.update_starvation(dt)

        # ── starvation check (fires mid-phase only when timer expires) ─
        # We check at phase boundaries (timer ≤ 0) rather than interrupting
        # mid-phase, which prevents flickering and matches real-world behaviour.

        if self.timer <= 0:
            self._advance(intersection)

    def get_status(self):
        return self._last_status

    # ── internal helpers ────────────────────────────────────────────────

    def _advance(self, intersection):
        """Move to the next phase, inserting pedestrian windows as needed."""

        # Check for a starving lane before advancing normally
        starving_lane = self._find_starving_lane(intersection)

        if starving_lane and not self._override_active:
            # Serve the starved lane for one phase, then resume
            self._override_active = True
            self._override_lane   = starving_lane
            self._resume_index    = self.phase_index   # come back here
            self._set_green(starving_lane, intersection)
            return

        if self._override_active:
            # Override is done; resume normal sequence
            self._override_active = False
            self._override_lane   = None
            self.phase_index      = self._resume_index
            # Fall through to normal advance below

        # Normal advance
        self.phase_index = (self.phase_index + 1) % len(self.phases)
        intersection.cycle_count += 1

        # Insert pedestrian crossing after index 1→2 and 3→0 transitions
        # (i.e. when phase_index becomes 2 or 0)
        if self.phase_index % 2 == 0 and self.ped_count < 2:
            self.ped_phase = True
            self.ped_timer = PEDESTRIAN_TIME
            self.ped_count += 1
            intersection.current_green = set()
            self._last_status = f"Pedestrian crossing   {self.ped_timer:.1f}s"
            return

        if self.phase_index == 0:
            self.ped_count = 0   # reset ped counter at cycle start

        self._start_next_phase(intersection)

    def _start_next_phase(self, intersection):
        lane = self.phases[self.phase_index]
        self._set_green(lane, intersection)

    def _set_green(self, lane, intersection):
        intersection.current_green = {lane}
        self.timer = self._compute_green(lane, intersection)
        self._last_status = f"Green: {lane}   {self.timer:.1f}s remaining"

    def _compute_green(self, lane, intersection) -> float:
        """
        Allocate green time proportionally to the lane's pressure share among
        all lanes.  Falls back to MIN_GREEN_TIME when all queues are empty.
        Night-mode: if every lane has fewer than ADAPTIVE_THRESHOLD vehicles,
        cap the budget at MIN_GREEN_TIME * 2 to avoid over-long empty phases.
        """
        pressures = {l: intersection.total_pressure(l) for l in LANE_NAMES}
        total     = sum(pressures.values())

        # Empty intersection — give the minimum slice and move on quickly
        if total == 0:
            return MIN_GREEN_TIME

        lane_pressure = pressures[lane]
        share         = lane_pressure / total          # 0.0 – 1.0

        # Night-mode budget shrink: all lanes have short queues
        all_short = all(
            intersection.queue_length(l) < ADAPTIVE_THRESHOLD
            for l in LANE_NAMES
        )
        budget = MIN_GREEN_TIME * 2 if all_short else MAX_GREEN_TIME

        raw   = share * budget
        green = max(MIN_GREEN_TIME, min(MAX_GREEN_TIME, raw))
        return green

    def _find_starving_lane(self, intersection) -> str | None:
        """
        Return the lane with the highest starvation timer that has exceeded
        MAX_WAIT_CAP, or None if no lane is starving.
        Skips the currently green lane (it isn't starving by definition).
        """
        worst_lane  = None
        worst_timer = MAX_WAIT_CAP   # threshold

        for lane in LANE_NAMES:
            if lane in intersection.current_green:
                continue
            if intersection.starvation_timers[lane] > worst_timer:
                worst_timer = intersection.starvation_timers[lane]
                worst_lane  = lane

        return worst_lane