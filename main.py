# main.py
import pygame
import sys

from config          import SCREEN_WIDTH, SCREEN_HEIGHT
from core            import Intersection
from algorithms      import FixedCycleController
from ui              import Renderer
from profiles        import VehicleSpawner

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Traffic Signal Optimizer")
    clock   = pygame.time.Clock()

    intersection = Intersection()
    controller   = FixedCycleController(green_time=20)
    controller.start(intersection)
    renderer     = Renderer(screen)
    spawner      = VehicleSpawner(profile_name='morning')

    while True:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        spawner.update(dt, intersection)
        controller.update(dt, intersection)
        intersection.update_clearing(dt)
        renderer.draw(intersection, controller)
        pygame.display.flip()

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()