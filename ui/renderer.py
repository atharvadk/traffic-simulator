# ui/renderer.py
import pygame
from config import LANE_NAMES

# Colors
BLACK      = (  0,   0,   0)
WHITE      = (255, 255, 255)
GRAY       = ( 60,  60,  60)
DARK_GRAY  = ( 30,  30,  30)
ROAD_COLOR = ( 50,  50,  50)
LINE_COLOR = (200, 200,   0)

GREEN_LIGHT  = (  0, 220,   0)
RED_LIGHT    = (220,   0,   0)
YELLOW_LIGHT = (220, 220,   0)
LIGHT_OFF    = ( 40,  40,  40)

VEHICLE_COLORS = {
    'two_wheeler':  ( 80, 160, 255),
    'four_wheeler': ( 60, 200, 100),
    'heavy':        (200, 120,  40),
    'emergency':    (255,  50,  50),
}

class Renderer:
    def __init__(self, screen):
        self.screen = screen
        self.w      = screen.get_width()
        self.h      = screen.get_height()

        self.cx = self.w // 2
        self.cy = self.h // 2

        self.road_width = 120
        self.lane_width = self.road_width // 2

        self.font_small  = pygame.font.SysFont("monospace", 14)
        self.font_medium = pygame.font.SysFont("monospace", 18)
        self.font_large  = pygame.font.SysFont("monospace", 22)

    def draw(self, intersection, controller):
        self.screen.fill(DARK_GRAY)
        self._draw_roads()
        self._draw_intersection_box()
        self._draw_lane_markings()
        self._draw_traffic_lights(intersection)
        self._draw_vehicles(intersection)
        self._draw_lane_labels()
        self._draw_status(controller, intersection)
        self._draw_legend()

    # ── roads ──────────────────────────────────────────────────────────
    def _draw_roads(self):
        cx, cy = self.cx, self.cy
        rw     = self.road_width

        pygame.draw.rect(self.screen, ROAD_COLOR,
                         (0, cy - rw // 2, self.w, rw))
        pygame.draw.rect(self.screen, ROAD_COLOR,
                         (cx - rw // 2, 0, rw, self.h))

    def _draw_intersection_box(self):
        cx, cy = self.cx, self.cy
        rw     = self.road_width
        pygame.draw.rect(self.screen, ROAD_COLOR,
                         (cx - rw // 2, cy - rw // 2, rw, rw))

    def _draw_lane_markings(self):
        cx, cy = self.cx, self.cy
        rw     = self.road_width

        for x in range(0, self.w, 30):
            if abs(x - cx) > rw // 2:
                pygame.draw.rect(self.screen, LINE_COLOR,
                                 (x, cy - 2, 16, 4))

        for y in range(0, self.h, 30):
            if abs(y - cy) > rw // 2:
                pygame.draw.rect(self.screen, LINE_COLOR,
                                 (cx - 2, y, 4, 16))

        # road edge lines
        pygame.draw.line(self.screen, GRAY,
                         (0, cy - rw // 2), (cx - rw // 2, cy - rw // 2), 1)
        pygame.draw.line(self.screen, GRAY,
                         (cx + rw // 2, cy - rw // 2), (self.w, cy - rw // 2), 1)
        pygame.draw.line(self.screen, GRAY,
                         (0, cy + rw // 2), (cx - rw // 2, cy + rw // 2), 1)
        pygame.draw.line(self.screen, GRAY,
                         (cx + rw // 2, cy + rw // 2), (self.w, cy + rw // 2), 1)

        pygame.draw.line(self.screen, GRAY,
                         (cx - rw // 2, 0), (cx - rw // 2, cy - rw // 2), 1)
        pygame.draw.line(self.screen, GRAY,
                         (cx - rw // 2, cy + rw // 2), (cx - rw // 2, self.h), 1)
        pygame.draw.line(self.screen, GRAY,
                         (cx + rw // 2, 0), (cx + rw // 2, cy - rw // 2), 1)
        pygame.draw.line(self.screen, GRAY,
                         (cx + rw // 2, cy + rw // 2), (cx + rw // 2, self.h), 1)

    # ── traffic lights ─────────────────────────────────────────────────
    def _draw_traffic_lights(self, intersection):
        cx, cy = self.cx, self.cy
        rw     = self.road_width
        offset = rw // 2 + 18

        positions = {
            'North': (cx + rw // 2 + 10, cy - offset - 30),
            'South': (cx - rw // 2 - 38, cy + offset),
            'East':  (cx + offset,        cy + rw // 2 + 10),
            'West':  (cx - offset - 38,   cy - rw // 2 - 38),
        }

        for lane, (lx, ly) in positions.items():
            self._draw_light_box(lx, ly, intersection.is_green(lane), lane)

    def _draw_light_box(self, x, y, is_green, label):
        box_w, box_h = 28, 76

        # shadow
        pygame.draw.rect(self.screen, (10, 10, 10),
                         (x + 3, y + 3, box_w, box_h), border_radius=6)
        # housing
        pygame.draw.rect(self.screen, (20, 20, 20),
                         (x, y, box_w, box_h), border_radius=6)
        pygame.draw.rect(self.screen, GRAY,
                         (x, y, box_w, box_h), 1, border_radius=6)

        red_color   = RED_LIGHT   if not is_green else LIGHT_OFF
        green_color = GREEN_LIGHT if is_green     else LIGHT_OFF

        # red
        pygame.draw.circle(self.screen, red_color,
                           (x + box_w // 2, y + 16), 10)
        if not is_green:
            pygame.draw.circle(self.screen, (255, 80, 80),
                               (x + box_w // 2 - 3, y + 12), 3)

        # yellow
        pygame.draw.circle(self.screen, LIGHT_OFF,
                           (x + box_w // 2, y + 38), 10)

        # green
        pygame.draw.circle(self.screen, green_color,
                           (x + box_w // 2, y + 60), 10)
        if is_green:
            pygame.draw.circle(self.screen, (80, 255, 120),
                               (x + box_w // 2 - 3, y + 56), 3)

        txt = self.font_small.render(label[0], True, WHITE)
        self.screen.blit(txt, (x + 9, y + box_h + 4))

    # ── vehicles ───────────────────────────────────────────────────────
    def _draw_vehicles(self, intersection):
        cx, cy = self.cx, self.cy
        rw     = self.road_width
        offset = rw // 2 + 10
        gap    = 22

        for lane, queue in intersection.queues.items():
            for i, vehicle in enumerate(queue[:10]):
                color = VEHICLE_COLORS[vehicle.type]
                dist  = offset + i * gap

                if lane == 'North':
                    x = cx - self.lane_width + 10
                    y = cy - dist - 16
                elif lane == 'South':
                    x = cx + 10
                    y = cy + dist
                elif lane == 'East':
                    x = cx + dist
                    y = cy - self.lane_width + 10
                elif lane == 'West':
                    x = cx - dist - 16
                    y = cy + 10

                # vehicle body
                pygame.draw.rect(self.screen, color,
                                 (x, y, 16, 16), border_radius=3)

                # darker outline
                darker = tuple(max(0, c - 60) for c in color)
                pygame.draw.rect(self.screen, darker,
                                 (x, y, 16, 16), 1, border_radius=3)

                # emergency flash border
                if vehicle.type == 'emergency':
                    pygame.draw.rect(self.screen, WHITE,
                                     (x - 1, y - 1, 18, 18), 2, border_radius=3)

                # wait time indicator — tiny dot turns red if waiting long
                if vehicle.wait_time > 15:
                    pygame.draw.circle(self.screen, (255, 80, 80),
                                       (x + 14, y + 2), 3)

    # ── lane labels ────────────────────────────────────────────────────
    def _draw_lane_labels(self):
        cx, cy = self.cx, self.cy
        rw     = self.road_width

        labels = {
            'North': (cx - 26, cy - rw // 2 - 50),
            'South': (cx - 26, cy + rw // 2 + 24),
            'East':  (cx + rw // 2 + 24, cy - 10),
            'West':  (cx - rw // 2 - 58, cy - 10),
        }

        for lane, (lx, ly) in labels.items():
            txt = self.font_medium.render(lane, True, WHITE)
            self.screen.blit(txt, (lx, ly))

    # ── status panel ───────────────────────────────────────────────────
    def _draw_status(self, controller, intersection):
        # background panel
        panel = pygame.Surface((420, 140), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 140))
        self.screen.blit(panel, (10, 10))

        # current phase
        status = controller.get_status()
        txt    = self.font_large.render(status, True, (255, 220, 50))
        self.screen.blit(txt, (20, 18))

        # cycle + cleared + avg wait
        summary = (
            f"Cycle: {intersection.cycle_count}   "
            f"Cleared: {intersection.cleared_count}   "
            f"Avg wait: {intersection.avg_wait_time:.1f}s"
        )
        txt = self.font_medium.render(summary, True, (180, 180, 180))
        self.screen.blit(txt, (20, 46))

        # per lane info
        y = 74
        for lane in LANE_NAMES:
            q      = intersection.queue_length(lane)
            starve = intersection.starvation_timers[lane]
            pres   = intersection.total_pressure(lane)
            col    = (255, 100, 100) if intersection.is_starving(lane) else (200, 200, 200)

            # green indicator dot
            dot_col = GREEN_LIGHT if intersection.is_green(lane) else RED_LIGHT
            pygame.draw.circle(self.screen, dot_col, (28, y + 7), 5)

            txt = self.font_small.render(
                f"{lane:<6} q:{q:<3} wait:{starve:>5.1f}s  pressure:{pres:>5.1f}",
                True, col)
            self.screen.blit(txt, (38, y))
            y += 18

    # ── legend ─────────────────────────────────────────────────────────
    def _draw_legend(self):
        x, y = self.w - 200, 10
        panel = pygame.Surface((190, 100), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 140))
        self.screen.blit(panel, (x - 5, y))

        items = [
            ('two_wheeler',  'Two wheeler'),
            ('four_wheeler', 'Four wheeler'),
            ('heavy',        'Heavy vehicle'),
            ('emergency',    'Emergency'),
        ]

        for i, (vtype, label) in enumerate(items):
            color = VEHICLE_COLORS[vtype]
            pygame.draw.rect(self.screen, color,
                             (x, y + 6 + i * 22, 14, 14), border_radius=2)
            txt = self.font_small.render(label, True, (200, 200, 200))
            self.screen.blit(txt, (x + 20, y + 6 + i * 22))