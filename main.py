# main.py
import pygame
import sys

from config          import SCREEN_WIDTH, SCREEN_HEIGHT
from core            import Intersection
from algorithms      import FixedCycleController
from algorithms.greedy import GreedyCycleController
from ui              import Renderer
from profiles        import VehicleSpawner

ALGO_LABEL = {
    1: "Fixed Cycle",
    2: "Greedy Adaptive",
}

def make_controller(algo_id):
    if algo_id == 1:
        return FixedCycleController(green_time=20)
    return GreedyCycleController()

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Traffic Signal Optimizer")
    clock = pygame.time.Clock()

    current_algo = 1
    intersection = Intersection()
    controller   = make_controller(current_algo)
    controller.start(intersection)
    renderer     = Renderer(screen)
    spawner      = VehicleSpawner(profile_name='morning')

    font = pygame.font.SysFont("monospace", 15)

    while True:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1 and current_algo != 1:
                    current_algo = 1
                    intersection = Intersection()
                    controller   = make_controller(current_algo)
                    controller.start(intersection)
                    spawner      = VehicleSpawner(profile_name='morning')

                elif event.key == pygame.K_2 and current_algo != 2:
                    current_algo = 2
                    intersection = Intersection()
                    controller   = make_controller(current_algo)
                    controller.start(intersection)
                    spawner      = VehicleSpawner(profile_name='morning')

        spawner.update(dt, intersection)
        controller.update(dt, intersection)
        intersection.update_clearing(dt)
        renderer.draw(intersection, controller)

        # Algorithm label overlay (bottom-left)
        label = f"[1] Fixed  [2] Greedy    Active: {ALGO_LABEL[current_algo]}"
        surf  = font.render(label, True, (220, 220, 100))
        screen.blit(surf, (12, SCREEN_HEIGHT - 28))

        pygame.display.flip()

if __name__ == "__main__":
    main()