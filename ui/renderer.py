# ui/renderer.py
import pygame
import math
from config import LANE_NAMES, LANE_WIDTH

# ── Palette ────────────────────────────────────────────────────────────
BG_DARK       = (  8,  10,  18)
BG_PANEL      = ( 14,  18,  30)
ROAD_COLOR    = ( 24,  28,  40)
ROAD_EDGE     = ( 36,  42,  58)
DIVIDER       = ( 60,  70, 100)
LANE_MARK     = ( 45,  55,  80)

ACCENT_CYAN   = (  0, 210, 255)
ACCENT_GREEN  = ( 40, 255, 140)
ACCENT_ORANGE = (255, 155,  45)
ACCENT_RED    = (255,  55,  75)
ACCENT_YELLOW = (255, 215,  45)
ACCENT_PURPLE = (170,  90, 255)

WHITE         = (255, 255, 255)
GRAY_LIGHT    = (170, 182, 205)
GRAY_MID      = ( 90, 105, 135)
GRAY_DARK     = ( 32,  40,  60)

GREEN_LIGHT   = ( 40, 255, 110)
RED_LIGHT     = (255,  45,  75)
LIGHT_OFF     = ( 20,  26,  42)

VEHICLE_COLORS = {
    'two_wheeler':  ( 50, 180, 255),
    'four_wheeler': ( 50, 220, 130),
    'heavy':        (255, 150,  50),
    'emergency':    (255,  50,  80),
}

ALGO_COLORS = {
    'fixed':  (110, 130, 255),
    'greedy': ( 40, 215, 140),
    'dp':     (255, 185,  50),
}

PROFILE_COLORS = {
    'morning':   (255, 195,  75),
    'afternoon': ( 70, 215, 255),
    'evening':   (255, 125,  55),
    'night':     (135,  95, 255),
}

DIRECTION_SYMBOLS = {
    'left':     '←',
    'straight': '↑',
    'right':    '→',
}


class Renderer:
    def __init__(self, screen):
        self.screen     = screen
        self.w          = screen.get_width()
        self.h          = screen.get_height()
        self.cx         = self.w // 2
        self.cy         = self.h // 2
        self.lw         = LANE_WIDTH
        self.road_width = self.lw * 3   # 3 lanes per arm
        self._pulse     = 0.0

        self.font_xs     = pygame.font.SysFont("consolas", 11)
        self.font_small  = pygame.font.SysFont("consolas", 13)
        self.font_medium = pygame.font.SysFont("consolas", 16)
        self.font_large  = pygame.font.SysFont("consolas", 20)
        self.font_title  = pygame.font.SysFont("consolas", 22, bold=True)

    # ── lane geometry helpers ──────────────────────────────────────────
    def _lane_rect(self, lane):
        """Returns (x, y, w, h) of the lane strip on screen."""
        cx, cy = self.cx, self.cy
        lw     = self.lw
        rw     = self.road_width
        arm_len = max(cx, cy)  # extend to screen edge

        if lane == 'North-Left':
            return (cx - lw * 2, 0, lw, cy - rw // 2)
        elif lane == 'North-Right':
            return (cx - lw,     0, lw, cy - rw // 2)
        elif lane == 'North-Exit':
            return (cx,          0, lw, cy - rw // 2)

        elif lane == 'South-Left':
            return (cx + lw,     cy + rw // 2, lw, self.h - cy - rw // 2)
        elif lane == 'South-Right':
            return (cx,          cy + rw // 2, lw, self.h - cy - rw // 2)
        elif lane == 'South-Exit':
            return (cx - lw * 2, cy + rw // 2, lw, self.h - cy - rw // 2)

        elif lane == 'East-Left':
            return (cx + rw // 2, cy - lw * 2, self.w - cx - rw // 2, lw)
        elif lane == 'East-Right':
            return (cx + rw // 2, cy - lw,     self.w - cx - rw // 2, lw)
        elif lane == 'East-Exit':
            return (cx + rw // 2, cy,           self.w - cx - rw // 2, lw)

        elif lane == 'West-Left':
            return (0, cy + lw,     cx - rw // 2, lw)
        elif lane == 'West-Right':
            return (0, cy,          cx - rw // 2, lw)
        elif lane == 'West-Exit':
            return (0, cy - lw * 2, cx - rw // 2, lw)

        return (0, 0, 0, 0)

    def _lane_center(self, lane):
        r = self._lane_rect(lane)
        return (r[0] + r[2] // 2, r[1] + r[3] // 2)

    # ── main draw ──────────────────────────────────────────────────────
    def draw(self, intersection, controller, algo_name='fixed',
             emergency=None, profile_name='morning',
             mouse_pos=(0, 0), animator=None):
        self._pulse += 0.05
        self.screen.fill(BG_DARK)

        self._draw_grid()
        self._draw_roads()
        self._draw_lane_markings()
        self._draw_dividers()
        self._draw_zebra_crossings()
        self._draw_exit_lane_indicators()
        self._draw_direction_signs()
        self._draw_traffic_lights(intersection)
        self._draw_vehicles(intersection, mouse_pos)
        if animator:
            self._draw_crossing_vehicles(animator, mouse_pos)
        self._draw_hud(controller, intersection, algo_name, emergency, profile_name)
        self._draw_controls_box(algo_name, profile_name)
        self._draw_legend()

        if emergency and emergency.active:
            self._draw_emergency_overlay(emergency)

    # ── background grid ────────────────────────────────────────────────
    def _draw_grid(self):
        for x in range(0, self.w, 40):
            pygame.draw.line(self.screen, (14, 17, 28), (x, 0), (x, self.h))
        for y in range(0, self.h, 40):
            pygame.draw.line(self.screen, (14, 17, 28), (0, y), (self.w, y))

    # ── roads ──────────────────────────────────────────────────────────
    def _draw_roads(self):
        cx, cy = self.cx, self.cy
        rw     = self.road_width

        # horizontal road
        pygame.draw.rect(self.screen, ROAD_COLOR,
                         (0, cy - rw // 2, self.w, rw))
        # vertical road
        pygame.draw.rect(self.screen, ROAD_COLOR,
                         (cx - rw // 2, 0, rw, self.h))
        # intersection box
        pygame.draw.rect(self.screen, ROAD_COLOR,
                         (cx - rw // 2, cy - rw // 2, rw, rw))

    # ── lane markings (dashes) ─────────────────────────────────────────
    def _draw_lane_markings(self):
        cx, cy = self.cx, self.cy
        lw     = self.lw
        rw     = self.road_width
        dash   = 14
        gap    = 10

        # North vertical dashes between N-Left and N-Right
        y = 0
        while y < cy - rw // 2:
            pygame.draw.line(self.screen, LANE_MARK,
                             (cx - lw, y), (cx - lw, y + dash), 1)
            y += dash + gap

        # South vertical dashes
        y = cy + rw // 2
        while y < self.h:
            pygame.draw.line(self.screen, LANE_MARK,
                             (cx + lw, y), (cx + lw, y + dash), 1)
            y += dash + gap

        # East horizontal dashes
        x = cx + rw // 2
        while x < self.w:
            pygame.draw.line(self.screen, LANE_MARK,
                             (x, cy - lw), (x + dash, cy - lw), 1)
            x += dash + gap

        # West horizontal dashes
        x = 0
        while x < cx - rw // 2:
            pygame.draw.line(self.screen, LANE_MARK,
                             (x, cy + lw), (x + dash, cy + lw), 1)
            x += dash + gap

    # ── dividers (solid line separating incoming from exit) ────────────
    def _draw_dividers(self):
        cx, cy = self.cx, self.cy
        lw     = self.lw
        rw     = self.road_width

        # North divider — between N-Right and N-Exit
        pygame.draw.line(self.screen, DIVIDER,
                         (cx, 0), (cx, cy - rw // 2), 2)

        # South divider — between S-Right and S-Exit
        pygame.draw.line(self.screen, DIVIDER,
                         (cx - lw, cy + rw // 2), (cx - lw, self.h), 2)

        # East divider
        pygame.draw.line(self.screen, DIVIDER,
                         (cx + rw // 2, cy), (self.w, cy), 2)

        # West divider
        pygame.draw.line(self.screen, DIVIDER,
                         (0, cy - lw), (cx - rw // 2, cy - lw), 2)

    # ── zebra crossings ────────────────────────────────────────────────
    def _draw_zebra_crossings(self):
        cx, cy = self.cx, self.cy
        rw     = self.road_width
        surf   = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        stripe = 5
        gap    = 4
        length = 16

        # North
        for i in range(rw // (stripe + gap)):
            x = cx - rw // 2 + i * (stripe + gap)
            pygame.draw.rect(surf, (255, 255, 255, 28),
                             (x, cy - rw // 2 - length, stripe, length))
        # South
        for i in range(rw // (stripe + gap)):
            x = cx - rw // 2 + i * (stripe + gap)
            pygame.draw.rect(surf, (255, 255, 255, 28),
                             (x, cy + rw // 2, stripe, length))
        # East
        for i in range(rw // (stripe + gap)):
            y = cy - rw // 2 + i * (stripe + gap)
            pygame.draw.rect(surf, (255, 255, 255, 28),
                             (cx + rw // 2, y, length, stripe))
        # West
        for i in range(rw // (stripe + gap)):
            y = cy - rw // 2 + i * (stripe + gap)
            pygame.draw.rect(surf, (255, 255, 255, 28),
                             (cx - rw // 2 - length, y, length, stripe))

        self.screen.blit(surf, (0, 0))

    # ── exit lane indicators ───────────────────────────────────────────
    def _draw_exit_lane_indicators(self):
        """Subtle tint on exit lanes so they're visually distinct."""
        exit_lanes = ['North-Exit', 'South-Exit', 'East-Exit', 'West-Exit']
        surf = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        for lane in exit_lanes:
            r = self._lane_rect(lane)
            pygame.draw.rect(surf, (0, 200, 100, 15), r)
            pygame.draw.rect(surf, (0, 200, 100, 40),
                             (r[0], r[1], r[2], r[3]), 1)
        self.screen.blit(surf, (0, 0))

    # ── direction signs ────────────────────────────────────────────────
    def _draw_direction_signs(self):
        cx, cy = self.cx, self.cy
        lw     = self.lw
        rw     = self.road_width

        signs = [
            # (x, y, symbol, label)
            (cx - lw * 2 + lw // 2, cy - rw // 2 - 38, '←', 'N-L'),
            (cx - lw      + lw // 2, cy - rw // 2 - 38, '↑', 'N-R'),
            (cx           + lw // 2, cy - rw // 2 - 38, '↑', 'N-X'),

            (cx + lw      + lw // 2, cy + rw // 2 + 8,  '←', 'S-L'),
            (cx           + lw // 2, cy + rw // 2 + 8,  '↑', 'S-R'),
            (cx - lw * 2  + lw // 2, cy + rw // 2 + 8,  '↑', 'S-X'),

            (cx + rw // 2 + 8,  cy - lw * 2 + lw // 2, '←', 'E-L'),
            (cx + rw // 2 + 8,  cy - lw      + lw // 2, '↑', 'E-R'),
            (cx + rw // 2 + 8,  cy           + lw // 2, '↑', 'E-X'),

            (cx - rw // 2 - 30, cy + lw      + lw // 2, '←', 'W-L'),
            (cx - rw // 2 - 30, cy           + lw // 2, '↑', 'W-R'),
            (cx - rw // 2 - 30, cy - lw * 2  + lw // 2, '↑', 'W-X'),
        ]

        for sx, sy, sym, label in signs:
            is_exit = label.endswith('X')
            col     = (0, 200, 100) if is_exit else ACCENT_CYAN

            # small sign box
            box_w = 22
            surf  = pygame.Surface((box_w, 28), pygame.SRCALPHA)
            pygame.draw.rect(surf, (*col, 40), (0, 0, box_w, 28), border_radius=4)
            pygame.draw.rect(surf, (*col, 100), (0, 0, box_w, 28), 1, border_radius=4)
            self.screen.blit(surf, (sx - box_w // 2, sy - 4))

            arrow = self.font_xs.render(sym, True, col)
            lbl   = self.font_xs.render(label, True,
                                        (120, 200, 120) if is_exit else GRAY_MID)
            self.screen.blit(arrow, (sx - arrow.get_width() // 2, sy))
            self.screen.blit(lbl,   (sx - lbl.get_width() // 2,   sy + 13))

    # ── traffic lights ─────────────────────────────────────────────────
    def _draw_traffic_lights(self, intersection):
        cx, cy = self.cx, self.cy
        lw     = self.lw
        rw     = self.road_width

        # Each incoming lane gets its own signal box
        # attached with a thin line to the lane
        lane_signals = {
            'North-Left':  (cx - lw * 2 + lw // 2, cy - rw // 2 - 90),
            'North-Right': (cx - lw      + lw // 2, cy - rw // 2 - 90),
            'South-Left':  (cx + lw      + lw // 2, cy + rw // 2 + 55),
            'South-Right': (cx           + lw // 2, cy + rw // 2 + 55),
            'East-Left':   (cx + rw // 2 + 55,      cy - lw * 2 + lw // 2),
            'East-Right':  (cx + rw // 2 + 55,      cy - lw      + lw // 2),
            'West-Left':   (cx - rw // 2 - 75,      cy + lw      + lw // 2),
            'West-Right':  (cx - rw // 2 - 75,      cy           + lw // 2),
        }

        for lane, (sx, sy) in lane_signals.items():
            is_green = intersection.is_green(lane)
            lc       = self._lane_center(lane)

            # connector line from lane center to signal
            pygame.draw.line(self.screen, GRAY_DARK,
                             lc, (sx, sy), 1)

            self._draw_signal_box(sx, sy, is_green, lane)

    def _draw_signal_box(self, cx, cy, is_green, lane_name):
        bw, bh = 24, 60

        # glow effect when green
        if is_green:
            r = int(3 + 2 * math.sin(self._pulse))
            gsurf = pygame.Surface((bw + r * 2, bh + r * 2), pygame.SRCALPHA)
            pygame.draw.rect(gsurf, (*ACCENT_GREEN, 50),
                             (0, 0, bw + r * 2, bh + r * 2), border_radius=6)
            self.screen.blit(gsurf, (cx - bw // 2 - r, cy - bh // 2 - r))

        # housing
        pygame.draw.rect(self.screen, (6, 8, 16),
                         (cx - bw // 2 + 2, cy - bh // 2 + 2, bw, bh),
                         border_radius=5)
        pygame.draw.rect(self.screen, (18, 24, 40),
                         (cx - bw // 2, cy - bh // 2, bw, bh),
                         border_radius=5)
        pygame.draw.rect(self.screen, GRAY_DARK,
                         (cx - bw // 2, cy - bh // 2, bw, bh),
                         1, border_radius=5)

        # red light
        rc = RED_LIGHT if not is_green else LIGHT_OFF
        pygame.draw.circle(self.screen, rc, (cx, cy - bh // 2 + 12), 8)
        if not is_green:
            pygame.draw.circle(self.screen, (255, 120, 120),
                               (cx - 2, cy - bh // 2 + 9), 2)

        # yellow
        pygame.draw.circle(self.screen, LIGHT_OFF, (cx, cy), 8)

        # green light
        gc = GREEN_LIGHT if is_green else LIGHT_OFF
        pygame.draw.circle(self.screen, gc, (cx, cy + bh // 2 - 12), 8)
        if is_green:
            pygame.draw.circle(self.screen, (140, 255, 180),
                               (cx - 2, cy + bh // 2 - 15), 2)

        # lane name tag below box
        short = lane_name.replace('North', 'N').replace('South', 'S')\
                         .replace('East', 'E').replace('West', 'W')\
                         .replace('-Left', '-L').replace('-Right', '-R')
        tag = self.font_xs.render(short, True,
                                  ACCENT_GREEN if is_green else GRAY_MID)
        self.screen.blit(tag, (cx - tag.get_width() // 2, cy + bh // 2 + 4))

    # ── queued vehicles ────────────────────────────────────────────────
    def _draw_vehicles(self, intersection, mouse_pos):
        cx, cy = self.cx, self.cy
        lw     = self.lw
        rw     = self.road_width
        vw, vh = 11, 15
        gap    = 17
        offset = rw // 2 + 6
        hovered = None

        # position function per lane
        def pos(lane, i):
            if lane == 'North-Left':
                return (cx - lw * 2 + (lw - vw) // 2,
                        cy - offset - i * gap - vh)
            elif lane == 'North-Right':
                return (cx - lw + (lw - vw) // 2,
                        cy - offset - i * gap - vh)
            elif lane == 'South-Left':
                return (cx + lw + (lw - vw) // 2,
                        cy + offset + i * gap)
            elif lane == 'South-Right':
                return (cx + (lw - vw) // 2,
                        cy + offset + i * gap)
            elif lane == 'East-Left':
                return (cx + offset + i * gap,
                        cy - lw * 2 + (lw - vh) // 2)
            elif lane == 'East-Right':
                return (cx + offset + i * gap,
                        cy - lw + (lw - vh) // 2)
            elif lane == 'West-Left':
                return (cx - offset - i * gap - vw,
                        cy + lw + (lw - vh) // 2)
            elif lane == 'West-Right':
                return (cx - offset - i * gap - vw,
                        cy + (lw - vh) // 2)
            return (0, 0)

        for lane, queue in intersection.queues.items():
            for i, vehicle in enumerate(queue[:20]):
                vx, vy = pos(lane, i)
                color  = VEHICLE_COLORS[vehicle.type]

                # emergency pulse glow
                if vehicle.type == 'emergency':
                    pa = int(100 + 80 * math.sin(self._pulse * 3))
                    gs = pygame.Surface((vw + 8, vh + 8), pygame.SRCALPHA)
                    pygame.draw.rect(gs, (*ACCENT_RED, pa),
                                     (0, 0, vw + 8, vh + 8), border_radius=4)
                    self.screen.blit(gs, (vx - 4, vy - 4))

                # body
                pygame.draw.rect(self.screen, color,
                                 (vx, vy, vw, vh), border_radius=3)
                # shine
                shine = tuple(min(255, c + 55) for c in color)
                pygame.draw.rect(self.screen, shine,
                                 (vx + 2, vy + 2, vw - 4, 3), border_radius=1)
                # outline
                darker = tuple(max(0, c - 65) for c in color)
                pygame.draw.rect(self.screen, darker,
                                 (vx, vy, vw, vh), 1, border_radius=3)

                # direction arrow on vehicle
                if vehicle.direction:
                    sym = DIRECTION_SYMBOLS.get(vehicle.direction, '')
                    at  = self.font_xs.render(sym, True, WHITE)
                    self.screen.blit(at, (vx + 1, vy + vh // 2 - 5))

                # wait dot
                if vehicle.wait_time > 15:
                    pygame.draw.circle(self.screen, ACCENT_RED,
                                       (vx + vw - 1, vy + 2), 3)

                # hover
                if pygame.Rect(vx, vy, vw, vh).collidepoint(mouse_pos):
                    hovered = (vehicle, vx, vy)

        if hovered:
            self._draw_tooltip(*hovered)

    # ── crossing vehicle animations ────────────────────────────────────
    def _draw_crossing_vehicles(self, animator, mouse_pos):
        hovered = None
        for cv in animator.get_active():
            x, y  = cv.pos
            color = cv.color
            vw, vh = 11, 15

            # trail
            for tx, ty, alpha in cv.trail:
                a = int(alpha * 80)
                if a <= 0:
                    continue
                ts = pygame.Surface((vw, vh), pygame.SRCALPHA)
                pygame.draw.rect(ts, (*color, a), (0, 0, vw, vh), border_radius=3)
                self.screen.blit(ts, (int(tx) - vw // 2, int(ty) - vh // 2))

            # vehicle dot
            pygame.draw.rect(self.screen, color,
                             (x - vw // 2, y - vh // 2, vw, vh), border_radius=3)
            shine = tuple(min(255, c + 55) for c in color)
            pygame.draw.rect(self.screen, shine,
                             (x - vw // 2 + 2, y - vh // 2 + 2, vw - 4, 3),
                             border_radius=1)

            if pygame.Rect(x - vw // 2, y - vh // 2, vw, vh).collidepoint(mouse_pos):
                hovered = (cv.vehicle, x - vw // 2, y - vh // 2)

        if hovered:
            self._draw_tooltip(*hovered)

    # ── tooltip on hover ───────────────────────────────────────────────
    def _draw_tooltip(self, vehicle, vx, vy):
        arm = vehicle.lane.replace('-Left', '').replace('-Right', '')
        line1 = f"{vehicle.type}  {arm} → {vehicle.exit_arm or '?'}"
        line2 = f"dir: {vehicle.direction or 'n/a'}   wait: {vehicle.wait_time:.1f}s"

        lines   = [line1, line2]
        pad     = 8
        lh      = self.font_small.get_height()
        tw      = max(self.font_small.size(l)[0] for l in lines) + pad * 2
        th      = lh * 2 + pad * 2
        tx      = max(0, min(vx - tw // 2, self.w - tw))
        ty      = max(0, vy - th - 10)

        surf = pygame.Surface((tw, th), pygame.SRCALPHA)
        pygame.draw.rect(surf, (8, 12, 26, 225), (0, 0, tw, th), border_radius=6)
        pygame.draw.rect(surf, (*ACCENT_CYAN, 130), (0, 0, tw, th), 1, border_radius=6)
        self.screen.blit(surf, (tx, ty))

        for j, line in enumerate(lines):
            col = ACCENT_CYAN if j == 0 else GRAY_LIGHT
            txt = self.font_small.render(line, True, col)
            self.screen.blit(txt, (tx + pad, ty + pad + j * lh))

    # ── HUD (top left) ─────────────────────────────────────────────────
    def _draw_hud(self, controller, intersection, algo_name, emergency, profile_name):
        pw, ph = 400, 260
        surf   = pygame.Surface((pw, ph), pygame.SRCALPHA)
        pygame.draw.rect(surf, (6, 10, 22, 215), (0, 0, pw, ph), border_radius=10)
        pygame.draw.rect(surf, (*ACCENT_CYAN, 35), (0, 0, pw, ph), 1, border_radius=10)
        self.screen.blit(surf, (10, 10))

        # top accent bar
        pygame.draw.rect(self.screen, ALGO_COLORS.get(algo_name, ACCENT_CYAN),
                         (10, 10, pw, 3), border_radius=2)

        # status
        if emergency and emergency.active:
            status = emergency.get_status()
            col    = ACCENT_RED if emergency.flash_on else (150, 28, 48)
        else:
            status = controller.get_status()
            col    = ACCENT_YELLOW

        txt = self.font_title.render(status, True, col)
        self.screen.blit(txt, (20, 20))

        # metrics
        m = (f"CYC:{intersection.cycle_count:<4} "
             f"CLR:{intersection.cleared_count:<5} "
             f"AVG:{intersection.avg_wait_time:>5.1f}s")
        self.screen.blit(self.font_medium.render(m, True, GRAY_LIGHT), (20, 48))

        pygame.draw.line(self.screen, GRAY_DARK, (20, 70), (pw - 10, 70), 1)

        # per lane rows with pressure bars
        y = 78
        for lane in LANE_NAMES:
            q       = intersection.queue_length(lane)
            starve  = intersection.starvation_timers[lane]
            pres    = intersection.total_pressure(lane)
            is_g    = intersection.is_green(lane)
            starving = intersection.is_starving(lane)

            r   = int(5 + 2 * math.sin(self._pulse)) if is_g else 4
            dc  = GREEN_LIGHT if is_g else (ACCENT_RED if starving else GRAY_DARK)
            pygame.draw.circle(self.screen, dc, (24, y + 8), r)

            # pressure bar
            bx, by, bw, bh = 36, y + 2, 120, 9
            pygame.draw.rect(self.screen, GRAY_DARK, (bx, by, bw, bh), border_radius=3)
            if pres > 0:
                fill = min(bw, int((pres / 15.0) * bw))
                bc   = GREEN_LIGHT if is_g else (ACCENT_RED if starving else ACCENT_CYAN)
                pygame.draw.rect(self.screen, bc, (bx, by, fill, bh), border_radius=3)

            short = lane.replace('North', 'N').replace('South', 'S')\
                        .replace('East', 'E').replace('West', 'W')\
                        .replace('-Left', '-L').replace('-Right', '-R')
            row = f"{short:<6} q:{q:<2} w:{starve:>4.0f}s p:{pres:>4.1f}"
            rc  = (255, 100, 100) if starving else GRAY_LIGHT
            self.screen.blit(self.font_xs.render(row, True, rc), (165, y + 1))
            y += 22

    # ── controls box (bottom right) ────────────────────────────────────
    def _draw_controls_box(self, algo_name, profile_name):
        bw, bh = 340, 130
        bx     = self.w - bw - 10
        by     = self.h - bh - 10

        surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
        pygame.draw.rect(surf, (6, 10, 22, 215), (0, 0, bw, bh), border_radius=10)
        pygame.draw.rect(surf, (*ACCENT_CYAN, 35), (0, 0, bw, bh), 1, border_radius=10)
        self.screen.blit(surf, (bx, by))

        # header
        header = self.font_small.render("CONTROLS", True, ACCENT_CYAN)
        self.screen.blit(header, (bx + 12, by + 10))
        pygame.draw.line(self.screen, GRAY_DARK,
                         (bx + 10, by + 28), (bx + bw - 10, by + 28), 1)

        # algorithm buttons
        algos = [('1', 'Fixed', 'fixed'), ('2', 'Greedy', 'greedy'), ('3', 'DP', 'dp')]
        for i, (key, label, name) in enumerate(algos):
            active = algo_name == name
            col    = ALGO_COLORS[name]
            bsurf  = pygame.Surface((80, 24), pygame.SRCALPHA)
            bg     = (*col, 180) if active else (*col, 40)
            pygame.draw.rect(bsurf, bg, (0, 0, 80, 24), border_radius=5)
            pygame.draw.rect(bsurf, (*col, 150 if active else 80),
                             (0, 0, 80, 24), 1, border_radius=5)
            self.screen.blit(bsurf, (bx + 10 + i * 88, by + 36))

            tc = WHITE if active else col
            kt = self.font_xs.render(f"[{key}] {label}", True, tc)
            self.screen.blit(kt, (bx + 10 + i * 88 + 40 - kt.get_width() // 2,
                                  by + 42))

        # profile buttons
        profiles = [('P', 'Morning', 'morning'), ('P', 'Afternoon', 'afternoon'),
                    ('P', 'Evening', 'evening'), ('P', 'Night', 'night')]
        for i, (key, label, name) in enumerate(profiles):
            active = profile_name == name
            col    = PROFILE_COLORS[name]
            bsurf  = pygame.Surface((72, 20), pygame.SRCALPHA)
            bg     = (*col, 180) if active else (*col, 40)
            pygame.draw.rect(bsurf, bg, (0, 0, 72, 20), border_radius=4)
            pygame.draw.rect(bsurf, (*col, 150 if active else 80),
                             (0, 0, 72, 20), 1, border_radius=4)
            self.screen.blit(bsurf, (bx + 10 + i * 78, by + 68))

            tc = WHITE if active else col
            pt = self.font_xs.render(label, True, tc)
            self.screen.blit(pt, (bx + 10 + i * 78 + 36 - pt.get_width() // 2,
                                  by + 72))

        # emergency + fullscreen
        esurf = pygame.Surface((140, 22), pygame.SRCALPHA)
        pygame.draw.rect(esurf, (*ACCENT_RED, 60), (0, 0, 140, 22), border_radius=5)
        pygame.draw.rect(esurf, (*ACCENT_RED, 120), (0, 0, 140, 22), 1, border_radius=5)
        self.screen.blit(esurf, (bx + 10, by + 98))
        et = self.font_xs.render("[E] Emergency Vehicle", True, ACCENT_RED)
        self.screen.blit(et, (bx + 10 + 70 - et.get_width() // 2, by + 103))

        fsurf = pygame.Surface((140, 22), pygame.SRCALPHA)
        pygame.draw.rect(fsurf, (*GRAY_MID, 60), (0, 0, 140, 22), border_radius=5)
        pygame.draw.rect(fsurf, (*GRAY_MID, 120), (0, 0, 140, 22), 1, border_radius=5)
        self.screen.blit(fsurf, (bx + 160, by + 98))
        ft = self.font_xs.render("[F] Fullscreen", True, GRAY_LIGHT)
        self.screen.blit(ft, (bx + 160 + 70 - ft.get_width() // 2, by + 103))

    # ── legend (top right) ─────────────────────────────────────────────
    def _draw_legend(self):
        lw, lh = 170, 115
        lx     = self.w - lw - 10
        ly     = 10

        surf = pygame.Surface((lw, lh), pygame.SRCALPHA)
        pygame.draw.rect(surf, (6, 10, 22, 210), (0, 0, lw, lh), border_radius=8)
        pygame.draw.rect(surf, (*ACCENT_CYAN, 35), (0, 0, lw, lh), 1, border_radius=8)
        self.screen.blit(surf, (lx, ly))
        pygame.draw.rect(self.screen, ACCENT_CYAN, (lx, ly, lw, 3), border_radius=2)

        hdr = self.font_xs.render("VEHICLE TYPES", True, ACCENT_CYAN)
        self.screen.blit(hdr, (lx + 10, ly + 8))

        items = [
            ('two_wheeler',  '2-Wheeler'),
            ('four_wheeler', '4-Wheeler'),
            ('heavy',        'Heavy'),
            ('emergency',    'Emergency'),
        ]
        for i, (vt, label) in enumerate(items):
            col = VEHICLE_COLORS[vt]
            iy  = ly + 26 + i * 21
            pygame.draw.rect(self.screen, col,
                             (lx + 10, iy + 2, 10, 14), border_radius=2)
            shine = tuple(min(255, c + 55) for c in col)
            pygame.draw.rect(self.screen, shine,
                             (lx + 11, iy + 3, 8, 3), border_radius=1)
            self.screen.blit(
                self.font_xs.render(label, True, GRAY_LIGHT),
                (lx + 26, iy + 2))

    # ── emergency overlay ──────────────────────────────────────────────
    def _draw_emergency_overlay(self, emergency):
        if emergency.flash_on:
            bs = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            pygame.draw.rect(bs, (*ACCENT_RED, 160), (0, 0, self.w, self.h), 8)
            self.screen.blit(bs, (0, 0))

        col = ACCENT_RED if emergency.flash_on else (130, 25, 45)
        msg = f"⚠  EMERGENCY — {emergency.ev_lane} LANE  ⚠"
        txt = self.font_title.render(msg, True, col)
        tw  = txt.get_width()
        px  = self.w // 2 - tw // 2 - 12
        py  = self.h - 55

        ps = pygame.Surface((tw + 24, 36), pygame.SRCALPHA)
        pygame.draw.rect(ps, (18, 6, 10, 210), (0, 0, tw + 24, 36), border_radius=8)
        pygame.draw.rect(ps, (*col, 180), (0, 0, tw + 24, 36), 1, border_radius=8)
        self.screen.blit(ps, (px, py))
        self.screen.blit(txt, (px + 12, py + 6))