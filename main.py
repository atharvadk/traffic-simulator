# main.py
import pygame
import sys

from config       import SCREEN_WIDTH, SCREEN_HEIGHT
from core         import Vehicle, Intersection
from algorithms   import FixedCycleController

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Traffic Signal Optimizer")
    clock  = pygame.time.Clock()
    font   = pygame.font.SysFont("monospace", 22)

    intersection = Intersection()
    controller   = FixedCycleController(green_time=20)
    controller.start(intersection)

    while True:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        controller.update(dt, intersection)

        screen.fill((30, 30, 30))

        status = controller.get_status()
        text   = font.render(status, True, (255, 255, 255))
        screen.blit(text, (40, 40))

        cycle_text = font.render(f"Cycle count: {intersection.cycle_count}", True, (180, 180, 180))
        screen.blit(cycle_text, (40, 80))

        pygame.display.flip()

if __name__ == "__main__":
    main()