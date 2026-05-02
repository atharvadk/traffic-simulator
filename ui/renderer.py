# ui/renderer.py
import pygame
import pygame.gfxdraw
import math
from config import LANE_NAMES, LANE_WIDTH

# ── Palette ────────────────────────────────────────────────────────────
BG_DARK        = (  6,   8,  16)
ROAD_COLOR     = ( 22,  26,  38)
ROAD_DARK      = ( 16,  20,  30)
DIVIDER_COL    = ( 55,  65,  95)
LANE_DASH      = ( 40,  50,  75)
CURB_COL       = ( 35,  42,  62)

ACCENT_CYAN    = (  0, 210, 255)
ACCENT_GREEN   = ( 40, 255, 130)
ACCENT_RED     = (255,  50,  70)
ACCENT_YELLOW  = (255, 210,  40)
ACCENT_ORANGE  = (255, 150,  40)
ACCENT_PURPLE  = (160,  80, 255)

WHITE          = (255, 255, 255)
GRAY_LIGHT     = (165, 178, 205)
GRAY_MID       = ( 85, 100, 130)
GRAY_DARK      = ( 28,  36,  55)

GREEN_LIGHT    = ( 30, 255, 100)
RED_LIGHT      = (255,  40,  65)
YELLOW_LIGHT   = (255, 200,  30)
LIGHT_OFF      = ( 18,  22,  38)
LIGHT_HOUSING  = ( 14,  18,  30)

VEHICLE_COLORS = {
    'two_wheeler':  ( 45, 175, 255),
    'four_wheeler': ( 40, 215, 120),
    'heavy':        (255, 145,  40),
    'emergency':    (255,  45,  70),
}

ALGO_COLORS = {
    'fixed':  (105, 125, 255),
    'greedy': ( 35, 210, 130),
    'dp':     (255, 180,  45),
}

PROFILE_COLORS = {
    'morning':   (255, 190,  65),
    'afternoon': ( 60, 210, 255),
    'evening':   (255, 120,  50),
    'night':     (130,  88, 255),
}

DIRECTION_SYMBOLS = {
    'left':     '←',
    'straight': '↑',
    'right':    '→',
}


def _glow(screen, color, cx, cy, radius, alpha=60, layers=4):
    """Draw a soft glow circle using concentric alpha circles."""
    for i in range(layers, 0, -1):
        r   = radius + i * 3
        a   = alpha // i
        s   = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, a), (r, r), r)
        screen.blit(s, (cx - r, cy - r))


def _draw_rounded_rect_alpha(screen, color, rect, radius=8, alpha=200, border=0, border_color=None):
    s = pygame.Surface((rect[2], rect[3]), pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), (0, 0, rect[2], rect[3]), border_radius=radius)
    if border and border_color:
        pygame.draw.rect(s, (*border_color, min(255, alpha + 60)),
                         (0, 0, rect[2], rect[3]), border, border_radius=radius)
    screen.blit(s, (rect[0], rect[1]))


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.w      = screen.get_width()
        self.h      = screen.get_height()
        self.cx     = self.w // 2
        self.cy     = self.h // 2
        self.lw     = LANE_WIDTH        # width of one lane
        self.rw     = LANE_WIDTH * 3    # total road width (3 lanes per arm)
        self._pulse = 0.0

        self.font_xs     = pygame.font.SysFont("consolas", 11)
        self.font_small  = pygame.font.SysFont("consolas", 13)
        self.font_medium = pygame.font.SysFont("consolas", 16)
        self.font_large  = pygame.font.SysFont("consolas", 20)
        self.font_title  = pygame.font.SysFont("consolas", 22, bold=True)

    # ── geometry ───────────────────────────────────────────────────────
    # Road layout (from top, looking down):
    #
    #         cx-rw/2  cx-lw   cx    cx+rw/2
    #            |      |      |      |
    #   North:  [N-L]  [N-R]  [N-X]         (N-X = exit, right of divider at cx)
    #   South:  [S-X]  [S-R]  [S-L]         (S-X = exit, left of divider)
    #   East:   top=[E-L], mid=[E-R], bot=[E-X]
    #   West:   top=[W-X], mid=[W-R], bot=[W-L]

    def _arm_lanes(self):
        """Returns pixel x (for N/S) or y (for E/W) of each sub-lane center."""
        cx, cy = self.cx, self.cy
        lw     = self.lw
        rw     = self.rw
        return {
            # North/South — x positions of lane centers
            'North-Left':  cx - rw//2 + lw//2,
            'North-Right': cx - rw//2 + lw + lw//2,
            'North-Exit':  cx - rw//2 + lw*2 + lw//2,   # = cx + lw//2
            'South-Left':  cx - rw//2 + lw*2 + lw//2,   # mirror — exit on left
            'South-Right': cx - rw//2 + lw + lw//2,
            'South-Exit':  cx - rw//2 + lw//2,

            # East/West — y positions of lane centers
            'East-Left':  cy - rw//2 + lw//2,
            'East-Right': cy - rw//2 + lw + lw//2,
            'East-Exit':  cy - rw//2 + lw*2 + lw//2,
            'West-Left':  cy - rw//2 + lw*2 + lw//2,
            'West-Right': cy - rw//2 + lw + lw//2,
            'West-Exit':  cy - rw//2 + lw//2,
        }

    # ── main draw ──────────────────────────────────────────────────────
    def draw(self, intersection, controller, algo_name='fixed',
             emergency=None, profile_name='morning',
             mouse_pos=(0, 0), animator=None):
        self._pulse += 0.05
        self.screen.fill(BG_DARK)

        self._draw_grid()
        self._draw_roads()
        self._draw_intersection_box()
        self._draw_lane_details()
        self._draw_dividers()
        self._draw_zebra()
        self._draw_exit_tints()
        self._draw_lane_signs()
        self._draw_traffic_lights(intersection)
        self._draw_vehicles(intersection, mouse_pos)
        if animator:
            self._draw_crossing(animator, mouse_pos)
        self._draw_hud(controller, intersection, algo_name, emergency, profile_name)
        self._draw_controls(algo_name, profile_name)
        self._draw_legend()
        if emergency and emergency.active:
            self._draw_emergency_overlay(emergency)

    # ── grid ───────────────────────────────────────────────────────────
    def _draw_grid(self):
        for x in range(0, self.w, 40):
            pygame.draw.line(self.screen, (12, 15, 25), (x, 0), (x, self.h))
        for y in range(0, self.h, 40):
            pygame.draw.line(self.screen, (12, 15, 25), (0, y), (self.w, y))

    # ── roads ──────────────────────────────────────────────────────────
    def _draw_roads(self):
        cx, cy = self.cx, self.cy
        rw     = self.rw

        # road bodies
        pygame.draw.rect(self.screen, ROAD_COLOR,
                         (0, cy - rw//2, self.w, rw))
        pygame.draw.rect(self.screen, ROAD_COLOR,
                         (cx - rw//2, 0, rw, self.h))

        # subtle curb lines
        for offset in [0, rw]:
            pygame.draw.line(self.screen, CURB_COL,
                             (0, cy - rw//2 + offset),
                             (cx - rw//2, cy - rw//2 + offset), 1)
            pygame.draw.line(self.screen, CURB_COL,
                             (cx + rw//2, cy - rw//2 + offset),
                             (self.w, cy - rw//2 + offset), 1)
            pygame.draw.line(self.screen, CURB_COL,
                             (cx - rw//2 + offset, 0),
                             (cx - rw//2 + offset, cy - rw//2), 1)
            pygame.draw.line(self.screen, CURB_COL,
                             (cx - rw//2 + offset, cy + rw//2),
                             (cx - rw//2 + offset, self.h), 1)

    def _draw_intersection_box(self):
        cx, cy = self.cx, self.cy
        rw     = self.rw
        pygame.draw.rect(self.screen, ROAD_COLOR,
                         (cx - rw//2, cy - rw//2, rw, rw))
        # intersection corner dots
        r = 4
        for dx, dy in [(-rw//2, -rw//2), (rw//2, -rw//2),
                       (-rw//2,  rw//2), (rw//2,  rw//2)]:
            pygame.draw.circle(self.screen, CURB_COL, (cx+dx, cy+dy), r)

    # ── lane dashes ────────────────────────────────────────────────────
    def _draw_lane_details(self):
        cx, cy = self.cx, self.cy
        lw     = self.lw
        rw     = self.rw
        dash   = 12
        gap    = 10

        # North arm lane dividers (dashes between N-L and N-R)
        x1 = cx - rw//2 + lw
        y  = 0
        while y < cy - rw//2:
            pygame.draw.line(self.screen, LANE_DASH,
                             (x1, y), (x1, y + dash), 1)
            y += dash + gap

        # South arm
        x1 = cx - rw//2 + lw
        y  = cy + rw//2
        while y < self.h:
            pygame.draw.line(self.screen, LANE_DASH,
                             (x1, y), (x1, y + dash), 1)
            y += dash + gap

        # East arm lane dividers (dashes between E-L and E-R)
        y1 = cy - rw//2 + lw
        x  = cx + rw//2
        while x < self.w:
            pygame.draw.line(self.screen, LANE_DASH,
                             (x, y1), (x + dash, y1), 1)
            x += dash + gap

        # West arm
        y1 = cy - rw//2 + lw
        x  = 0
        while x < cx - rw//2:
            pygame.draw.line(self.screen, LANE_DASH,
                             (x, y1), (x + dash, y1), 1)
            x += dash + gap

    # ── dividers (solid — separates incoming from exit) ────────────────
    def _draw_dividers(self):
        cx, cy = self.cx, self.cy
        lw     = self.lw
        rw     = self.rw

        # North divider at cx (between N-R and N-X)
        pygame.draw.line(self.screen, DIVIDER_COL,
                         (cx, 0), (cx, cy - rw//2), 2)

        # South divider at cx - lw (between S-X and S-R)
        pygame.draw.line(self.screen, DIVIDER_COL,
                         (cx - lw, cy + rw//2), (cx - lw, self.h), 2)

        # East divider at cy (between E-R and E-X)
        pygame.draw.line(self.screen, DIVIDER_COL,
                         (cx + rw//2, cy), (self.w, cy), 2)

        # West divider at cy - lw (between W-X and W-R)
        pygame.draw.line(self.screen, DIVIDER_COL,
                         (0, cy - lw), (cx - rw//2, cy - lw), 2)

    # ── zebra crossings ────────────────────────────────────────────────
    def _draw_zebra(self):
        cx, cy = self.cx, self.cy
        rw     = self.rw
        surf   = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        sw     = 5
        sg     = 4
        sl     = 18

        # North
        for i in range(rw // (sw + sg)):
            x = cx - rw//2 + i * (sw + sg)
            pygame.draw.rect(surf, (255, 255, 255, 25),
                             (x, cy - rw//2 - sl, sw, sl))
        # South
        for i in range(rw // (sw + sg)):
            x = cx - rw//2 + i * (sw + sg)
            pygame.draw.rect(surf, (255, 255, 255, 25),
                             (x, cy + rw//2, sw, sl))
        # East
        for i in range(rw // (sw + sg)):
            y = cy - rw//2 + i * (sw + sg)
            pygame.draw.rect(surf, (255, 255, 255, 25),
                             (cx + rw//2, y, sl, sw))
        # West
        for i in range(rw // (sw + sg)):
            y = cy - rw//2 + i * (sw + sg)
            pygame.draw.rect(surf, (255, 255, 255, 25),
                             (cx - rw//2 - sl, y, sl, sw))

        self.screen.blit(surf, (0, 0))

    # ── exit lane tints ────────────────────────────────────────────────
    def _draw_exit_tints(self):
        cx, cy = self.cx, self.cy
        lw     = self.lw
        rw     = self.rw
        surf   = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
        col    = (0, 200, 100, 18)

        # North-Exit: rightmost lane of north arm
        pygame.draw.rect(surf, col, (cx, 0, lw, cy - rw//2))
        # South-Exit: leftmost lane of south arm
        pygame.draw.rect(surf, col, (cx - rw//2, cy + rw//2, lw, self.h - cy - rw//2))
        # East-Exit: bottom lane of east arm
        pygame.draw.rect(surf, col, (cx + rw//2, cy + lw, self.w - cx - rw//2, lw))
        # West-Exit: top lane of west arm
        pygame.draw.rect(surf, col, (0, cy - rw//2, cx - rw//2, lw))

        self.screen.blit(surf, (0, 0))

    # ── lane signs (arrows + labels) ──────────────────────────────────
    def _draw_lane_signs(self):
        cx, cy = self.cx, self.cy
        lw     = self.lw
        rw     = self.rw

        # (center_x, center_y, arrow, label, is_exit)
        signs = [
            # North arm — above intersection
            (cx - rw//2 + lw//2,       cy - rw//2 - 32, '←', 'N-L', False),
            (cx - rw//2 + lw + lw//2,  cy - rw//2 - 32, '↑', 'N-R', False),
            (cx + lw//2,               cy - rw//2 - 32, '↓', 'N-X', True),

            # South arm — below intersection
            (cx - rw//2 + lw//2,       cy + rw//2 + 16, '↑', 'S-X', True),
            (cx - rw//2 + lw + lw//2,  cy + rw//2 + 16, '↑', 'S-R', False),
            (cx - rw//2 + lw*2 + lw//2,cy + rw//2 + 16, '→', 'S-L', False),

            # East arm — right of intersection
            (cx + rw//2 + 16, cy - rw//2 + lw//2,       '↑', 'E-L', False),
            (cx + rw//2 + 16, cy - rw//2 + lw + lw//2,  '→', 'E-R', False),
            (cx + rw//2 + 16, cy + lw//2,                '←', 'E-X', True),

            # West arm — left of intersection
            (cx - rw//2 - 16, cy - rw//2 + lw//2 - lw,  '→', 'W-X', True),
            (cx - rw//2 - 16, cy - rw//2 + lw + lw//2,  '←', 'W-R', False),
            (cx - rw//2 - 16, cy - rw//2 + lw*2 + lw//2,'↓', 'W-L', False),
        ]

        for sx, sy, arrow, label, is_exit in signs:
            col  = (30, 200, 100) if is_exit else ACCENT_CYAN
            bw   = lw - 4
            bh   = 26

            _draw_rounded_rect_alpha(self.screen, col,
                                     (sx - bw//2, sy - bh//2, bw, bh),
                                     radius=5, alpha=35)
            _draw_rounded_rect_alpha(self.screen, col,
                                     (sx - bw//2, sy - bh//2, bw, bh),
                                     radius=5, alpha=0, border=1, border_color=col)

            at = self.font_xs.render(arrow, True, col)
            lt = self.font_xs.render(label, True,
                                     (80, 180, 80) if is_exit else GRAY_MID)
            self.screen.blit(at, (sx - at.get_width()//2, sy - bh//2 + 2))
            self.screen.blit(lt, (sx - lt.get_width()//2, sy + 2))

    # ── traffic lights — ONE per arm ───────────────────────────────────
    def _draw_traffic_lights(self, intersection):
        cx, cy = self.cx, self.cy
        rw     = self.rw
        lw     = self.lw

        # check yellow state from controller — passed via intersection flag
        arm_state = {}
        for arm, lanes in [
            ('North', ['North-Left', 'North-Right']),
            ('South', ['South-Left', 'South-Right']),
            ('East',  ['East-Left',  'East-Right']),
            ('West',  ['West-Left',  'West-Right']),
        ]:
            any_green  = any(intersection.is_green(l) for l in lanes)
            arm_state[arm] = 'green' if any_green else 'red'

        # override with yellow if controller says so
        if hasattr(intersection, '_yellow_arms'):
            for arm in intersection._yellow_arms:
                arm_state[arm] = 'yellow'

        poles = {
            'North': (cx - rw//2 - 20, cy - rw//2 - 10),
            'South': (cx + rw//2 + 20, cy + rw//2 + 10),
            'East':  (cx + rw//2 + 10, cy - rw//2 - 20),
            'West':  (cx - rw//2 - 10, cy + rw//2 + 20),
        }

        for arm, (px, py) in poles.items():
            self._draw_signal_pole(px, py, arm_state[arm], arm)

    def _draw_signal_pole(self, px, py, state, arm):
        pole_h = 55
        pole_w = 4
        dirs   = {
            'North': (0, -1), 'South': (0, 1),
            'East':  (1,  0), 'West': (-1, 0),
        }
        dx, dy = dirs[arm]
        tx = px + dx * pole_h
        ty = py + dy * pole_h

        pygame.draw.line(self.screen, (40, 50, 75), (px, py), (tx, ty), pole_w)
        pygame.draw.circle(self.screen, (30, 38, 58), (px, py), pole_w + 2)

        bw, bh = 28, 75
        hx = tx - bw//2
        hy = ty - bh//2

        # glow
        if state == 'green':
            _glow(self.screen, ACCENT_GREEN, tx, ty, 14, alpha=30, layers=3)
        elif state == 'yellow':
            _glow(self.screen, ACCENT_YELLOW, tx, ty, 14, alpha=30, layers=3)

        # housing
        pygame.draw.rect(self.screen, (4, 5, 10),
                        (hx + 3, hy + 3, bw, bh), border_radius=7)
        pygame.draw.rect(self.screen, LIGHT_HOUSING,
                        (hx, hy, bw, bh), border_radius=7)
        border_col = (ACCENT_GREEN if state == 'green'
                    else ACCENT_YELLOW if state == 'yellow'
                    else GRAY_DARK)
        pygame.draw.rect(self.screen, border_col,
                        (hx, hy, bw, bh), 1, border_radius=7)

        cx_l    = tx
        r_light = 9

        # red
        rc = RED_LIGHT if state == 'red' else LIGHT_OFF
        pygame.draw.circle(self.screen, rc, (cx_l, hy + 14), r_light)
        if state == 'red':
            _glow(self.screen, RED_LIGHT, cx_l, hy + 14, r_light, alpha=40, layers=2)
            pygame.draw.circle(self.screen, (255, 130, 130), (cx_l - 3, hy + 10), 3)

        # yellow
        yc = YELLOW_LIGHT if state == 'yellow' else LIGHT_OFF
        pygame.draw.circle(self.screen, yc, (cx_l, hy + 38), r_light)
        if state == 'yellow':
            _glow(self.screen, YELLOW_LIGHT, cx_l, hy + 38, r_light, alpha=50, layers=2)
            pygame.draw.circle(self.screen, (255, 240, 150), (cx_l - 3, hy + 34), 3)

        # green
        gc = GREEN_LIGHT if state == 'green' else LIGHT_OFF
        pygame.draw.circle(self.screen, gc, (cx_l, hy + 62), r_light)
        if state == 'green':
            _glow(self.screen, GREEN_LIGHT, cx_l, hy + 62, r_light, alpha=50, layers=3)
            pygame.draw.circle(self.screen, (150, 255, 190), (cx_l - 3, hy + 58), 3)

        lt = self.font_xs.render(arm[0], True,
                                ACCENT_GREEN if state == 'green'
                                else ACCENT_YELLOW if state == 'yellow'
                                else GRAY_MID)
        self.screen.blit(lt, (hx + bw//2 - lt.get_width()//2, hy + bh + 3))

    # ── queued vehicles ────────────────────────────────────────────────
    def _draw_vehicles(self, intersection, mouse_pos):
        cx, cy  = self.cx, self.cy
        lw      = self.lw
        rw      = self.rw
        vw, vh  = 12, 16
        gap     = 18
        offset  = rw//2 + 6
        hovered = None

        def vpos(lane, i):
            # x center of each lane
            lane_x = {
                'North-Left':  cx - rw//2 + lw//2,
                'North-Right': cx - rw//2 + lw + lw//2,
                'South-Left':  cx - rw//2 + lw*2 + lw//2,
                'South-Right': cx - rw//2 + lw + lw//2,
                'East-Left':   cy - rw//2 + lw//2,    # used as y
                'East-Right':  cy - rw//2 + lw + lw//2,
                'West-Left':   cy - rw//2 + lw*2 + lw//2,
                'West-Right':  cy - rw//2 + lw + lw//2,
            }
            if 'North' in lane:
                x = lane_x[lane] - vw//2
                y = cy - offset - i * gap - vh
                return x, y
            elif 'South' in lane:
                x = lane_x[lane] - vw//2
                y = cy + offset + i * gap
                return x, y
            elif 'East' in lane:
                x = cx + offset + i * gap
                y = lane_x[lane] - vh//2
                return x, y
            elif 'West' in lane:
                x = cx - offset - i * gap - vw
                y = lane_x[lane] - vh//2
                return x, y
            return 0, 0

        for lane, queue in intersection.queues.items():
            for i, vehicle in enumerate(queue[:22]):
                vx, vy = vpos(lane, i)
                color  = VEHICLE_COLORS[vehicle.type]

                # emergency glow
                if vehicle.type == 'emergency':
                    pa = int(90 + 70 * math.sin(self._pulse * 3))
                    gs = pygame.Surface((vw + 10, vh + 10), pygame.SRCALPHA)
                    pygame.draw.rect(gs, (*ACCENT_RED, pa),
                                     (0, 0, vw + 10, vh + 10), border_radius=5)
                    self.screen.blit(gs, (vx - 5, vy - 5))

                # body
                pygame.draw.rect(self.screen, color,
                                 (vx, vy, vw, vh), border_radius=3)
                # shine
                shine = tuple(min(255, c + 60) for c in color)
                pygame.draw.rect(self.screen, shine,
                                 (vx + 2, vy + 2, vw - 4, 3), border_radius=1)
                # outline
                dark = tuple(max(0, c - 70) for c in color)
                pygame.draw.rect(self.screen, dark,
                                 (vx, vy, vw, vh), 1, border_radius=3)

                # direction symbol
                if vehicle.direction:
                    sym = DIRECTION_SYMBOLS.get(vehicle.direction, '')
                    st  = self.font_xs.render(sym, True, WHITE)
                    self.screen.blit(st, (vx + 1, vy + vh//2 - 5))

                # wait dot
                if vehicle.wait_time > 15:
                    pygame.draw.circle(self.screen, ACCENT_RED,
                                       (vx + vw - 1, vy + 2), 3)

                if pygame.Rect(vx, vy, vw, vh).collidepoint(mouse_pos):
                    hovered = (vehicle, vx, vy)

        if hovered:
            self._draw_tooltip(*hovered)

    # ── crossing animations ────────────────────────────────────────────
    def _draw_crossing(self, animator, mouse_pos):
        vw, vh  = 12, 16
        hovered = None

        for cv in animator.get_active():
            x, y  = cv.pos
            color = cv.color

            # trail
            for tx, ty, a in cv.trail:
                if a <= 0:
                    continue
                ts = pygame.Surface((vw, vh), pygame.SRCALPHA)
                pygame.draw.rect(ts, (*color, int(a * 70)),
                                 (0, 0, vw, vh), border_radius=3)
                self.screen.blit(ts, (int(tx) - vw//2, int(ty) - vh//2))

            # body
            pygame.draw.rect(self.screen, color,
                             (x - vw//2, y - vh//2, vw, vh), border_radius=3)
            shine = tuple(min(255, c + 60) for c in color)
            pygame.draw.rect(self.screen, shine,
                             (x - vw//2 + 2, y - vh//2 + 2, vw - 4, 3),
                             border_radius=1)

            if pygame.Rect(x - vw//2, y - vh//2, vw, vh).collidepoint(mouse_pos):
                hovered = (cv.vehicle, x - vw//2, y - vh//2)

        if hovered:
            self._draw_tooltip(*hovered)

    # ── hover tooltip ──────────────────────────────────────────────────
    def _draw_tooltip(self, vehicle, vx, vy):
        arm   = vehicle.lane.replace('-Left', '').replace('-Right', '')
        line1 = f"{vehicle.type}  {arm} → {vehicle.exit_arm or '?'}"
        line2 = f"dir:{vehicle.direction or 'n/a'}  wait:{vehicle.wait_time:.1f}s"
        lines = [line1, line2]
        pad   = 8
        lh    = self.font_small.get_height()
        tw    = max(self.font_small.size(l)[0] for l in lines) + pad * 2
        th    = lh * 2 + pad * 2
        tx    = max(0, min(vx - tw//2, self.w - tw))
        ty    = max(0, vy - th - 10)

        _draw_rounded_rect_alpha(self.screen, (8, 12, 26),
                                 (tx, ty, tw, th), radius=6, alpha=225,
                                 border=1, border_color=ACCENT_CYAN)

        for j, line in enumerate(lines):
            col = ACCENT_CYAN if j == 0 else GRAY_LIGHT
            t   = self.font_small.render(line, True, col)
            self.screen.blit(t, (tx + pad, ty + pad + j * lh))

    # ── HUD top-left ───────────────────────────────────────────────────
    def _draw_hud(self, controller, intersection, algo_name, emergency, profile_name):
        pw, ph = 390, 268
        _draw_rounded_rect_alpha(self.screen, (6, 10, 20),
                                 (10, 10, pw, ph), radius=10, alpha=215,
                                 border=1, border_color=ACCENT_CYAN)

        # top color bar
        pygame.draw.rect(self.screen,
                         ALGO_COLORS.get(algo_name, ACCENT_CYAN),
                         (10, 10, pw, 3), border_radius=2)

        # status
        if emergency and emergency.active:
            status = emergency.get_status()
            scol   = ACCENT_RED if emergency.flash_on else (140, 25, 45)
        else:
            status = controller.get_status()
            scol   = ACCENT_YELLOW

        st = self.font_title.render(status, True, scol)
        self.screen.blit(st, (20, 20))

        # metrics
        m = (f"CYC:{intersection.cycle_count:<4} "
             f"CLR:{intersection.cleared_count:<5} "
             f"AVG:{intersection.avg_wait_time:>5.1f}s")
        self.screen.blit(self.font_medium.render(m, True, GRAY_LIGHT), (20, 48))

        pygame.draw.line(self.screen, GRAY_DARK, (20, 70), (pw, 70), 1)

        # per-lane rows
        y = 78
        for lane in LANE_NAMES:
            q        = intersection.queue_length(lane)
            starve   = intersection.starvation_timers[lane]
            pres     = intersection.total_pressure(lane)
            is_g     = intersection.is_green(lane)
            starving = intersection.is_starving(lane)

            # pulsing dot
            r  = int(5 + 2 * math.sin(self._pulse)) if is_g else 4
            dc = GREEN_LIGHT if is_g else (ACCENT_RED if starving else GRAY_DARK)
            if is_g:
                _glow(self.screen, GREEN_LIGHT, 24, y + 8, r, alpha=30, layers=2)
            pygame.draw.circle(self.screen, dc, (24, y + 8), r)

            # pressure bar bg
            bx, by_, bw, bh = 36, y + 3, 115, 8
            pygame.draw.rect(self.screen, GRAY_DARK,
                             (bx, by_, bw, bh), border_radius=3)
            if pres > 0:
                fill = min(bw, int((pres / 15.0) * bw))
                bc   = GREEN_LIGHT if is_g else (ACCENT_RED if starving else ACCENT_CYAN)
                pygame.draw.rect(self.screen, bc,
                                 (bx, by_, fill, bh), border_radius=3)

            short = (lane.replace('North', 'N').replace('South', 'S')
                        .replace('East',  'E').replace('West',  'W')
                        .replace('-Left', '-L').replace('-Right', '-R'))
            row = f"{short:<6} q:{q:<2} w:{starve:>4.0f}s p:{pres:>4.1f}"
            rc  = (255, 100, 100) if starving else GRAY_LIGHT
            self.screen.blit(self.font_xs.render(row, True, rc), (158, y + 1))
            y += 23

    # ── controls box — bottom right ─────────────────────────────────────
    def _draw_controls(self, algo_name, profile_name):
        bw, bh = 350, 138
        bx     = self.w - bw - 10
        by_    = self.h - bh - 10

        _draw_rounded_rect_alpha(self.screen, (6, 10, 20),
                                 (bx, by_, bw, bh), radius=10, alpha=215,
                                 border=1, border_color=ACCENT_CYAN)

        # header
        ht = self.font_small.render("CONTROLS", True, ACCENT_CYAN)
        self.screen.blit(ht, (bx + 12, by_ + 10))
        pygame.draw.line(self.screen, GRAY_DARK,
                         (bx + 10, by_ + 28), (bx + bw - 10, by_ + 28), 1)

        # algorithm buttons
        algos = [('1', 'Fixed', 'fixed'),
                 ('2', 'Greedy', 'greedy'),
                 ('3', 'DP', 'dp')]
        for i, (key, label, name) in enumerate(algos):
            active = algo_name == name
            col    = ALGO_COLORS[name]
            bx2    = bx + 10 + i * 108
            by2    = by_ + 36
            bw2    = 100
            bh2    = 24
            bg_a   = 180 if active else 45
            _draw_rounded_rect_alpha(self.screen, col,
                                     (bx2, by2, bw2, bh2),
                                     radius=5, alpha=bg_a,
                                     border=1, border_color=col)
            if active:
                _glow(self.screen, col, bx2 + bw2//2, by2 + bh2//2,
                      8, alpha=20, layers=2)
            tc = WHITE if active else col
            kt = self.font_xs.render(f"[{key}] {label}", True, tc)
            self.screen.blit(kt, (bx2 + bw2//2 - kt.get_width()//2,
                                  by2 + bh2//2 - kt.get_height()//2))

        # profile buttons
        profiles = [('P', 'Morning',   'morning'),
                    ('P', 'Afternoon', 'afternoon'),
                    ('P', 'Evening',   'evening'),
                    ('P', 'Night',     'night')]
        for i, (_, label, name) in enumerate(profiles):
            active = profile_name == name
            col    = PROFILE_COLORS[name]
            bx2    = bx + 10 + i * 82
            by2    = by_ + 70
            bw2    = 74
            bh2    = 20
            bg_a   = 180 if active else 45
            _draw_rounded_rect_alpha(self.screen, col,
                                     (bx2, by2, bw2, bh2),
                                     radius=4, alpha=bg_a,
                                     border=1, border_color=col)
            tc = WHITE if active else col
            pt = self.font_xs.render(label, True, tc)
            self.screen.blit(pt, (bx2 + bw2//2 - pt.get_width()//2,
                                  by2 + bh2//2 - pt.get_height()//2))

        # emergency + fullscreen
        for i, (label, col) in enumerate([
            ('[E] Emergency', ACCENT_RED),
            ('[F] Fullscreen', GRAY_MID),
        ]):
            bx2 = bx + 10 + i * 170
            by2 = by_ + 102
            bw2 = 158
            bh2 = 24
            _draw_rounded_rect_alpha(self.screen, col,
                                     (bx2, by2, bw2, bh2),
                                     radius=5, alpha=50,
                                     border=1, border_color=col)
            t = self.font_xs.render(label, True, col)
            self.screen.blit(t, (bx2 + bw2//2 - t.get_width()//2,
                                 by2 + bh2//2 - t.get_height()//2))

    # ── legend top-right ───────────────────────────────────────────────
    def _draw_legend(self):
        lw_box = 175
        lh_box = 112
        lx     = self.w - lw_box - 10
        ly     = 10

        _draw_rounded_rect_alpha(self.screen, (6, 10, 20),
                                 (lx, ly, lw_box, lh_box), radius=8, alpha=210,
                                 border=1, border_color=ACCENT_CYAN)
        pygame.draw.rect(self.screen, ACCENT_CYAN,
                         (lx, ly, lw_box, 3), border_radius=2)

        ht = self.font_xs.render("VEHICLE TYPES", True, ACCENT_CYAN)
        self.screen.blit(ht, (lx + 10, ly + 8))

        items = [('two_wheeler',  '2-Wheeler'),
                 ('four_wheeler', '4-Wheeler'),
                 ('heavy',        'Heavy'),
                 ('emergency',    'Emergency')]

        for i, (vt, label) in enumerate(items):
            col = VEHICLE_COLORS[vt]
            iy  = ly + 28 + i * 20
            pygame.draw.rect(self.screen, col,
                             (lx + 10, iy + 2, 11, 14), border_radius=2)
            shine = tuple(min(255, c + 55) for c in col)
            pygame.draw.rect(self.screen, shine,
                             (lx + 11, iy + 3, 9, 3), border_radius=1)
            t = self.font_xs.render(label, True, GRAY_LIGHT)
            self.screen.blit(t, (lx + 26, iy + 2))

    # ── emergency overlay ──────────────────────────────────────────────
    def _draw_emergency_overlay(self, emergency):
        if emergency.flash_on:
            bs = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            pygame.draw.rect(bs, (*ACCENT_RED, 150),
                             (0, 0, self.w, self.h), 8)
            self.screen.blit(bs, (0, 0))

        col = ACCENT_RED if emergency.flash_on else (120, 22, 42)
        msg = f"⚠  EMERGENCY — {emergency.ev_lane} LANE  ⚠"
        txt = self.font_title.render(msg, True, col)
        tw  = txt.get_width()
        px  = self.w//2 - tw//2 - 14
        py  = self.h - 56

        _draw_rounded_rect_alpha(self.screen, (16, 4, 8),
                                 (px, py, tw + 28, 36),
                                 radius=8, alpha=215,
                                 border=1, border_color=col)
        self.screen.blit(txt, (px + 14, py + 6))