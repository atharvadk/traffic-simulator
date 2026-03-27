# main.py
import pygame
import sys
import random

from config     import SCREEN_WIDTH, SCREEN_HEIGHT, LANE_NAMES
from core       import Intersection, Vehicle
from algorithms import FixedCycleController, GreedyController, DPController
from ui         import Renderer
from profiles   import VehicleSpawner, PROFILES
from emergency  import EmergencyHandler

PROFILE_NAMES = list(PROFILES.keys())  # ['morning', 'afternoon', 'evening', 'night']

def make_controller(name, intersection):
    if name == 'fixed':
        c = FixedCycleController(green_time=20)
    elif name == 'greedy':
        c = GreedyController()
    else:
        c = DPController()
    c.start(intersection)
    return c

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Traffic Signal Optimizer")
    clock = pygame.time.Clock()

    intersection    = Intersection()
    algo_name       = 'fixed'
    controller      = make_controller(algo_name, intersection)
    renderer        = Renderer(screen)
    spawner         = VehicleSpawner(profile_name='morning')
    emergency       = EmergencyHandler()
    profile_index   = 0

    while True:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:

                # algorithm switching
                if event.key == pygame.K_1:
                    intersection = Intersection()
                    algo_name    = 'fixed'
                    controller   = make_controller(algo_name, intersection)
                    emergency    = EmergencyHandler()

                if event.key == pygame.K_2:
                    intersection = Intersection()
                    algo_name    = 'greedy'
                    controller   = make_controller(algo_name, intersection)
                    emergency    = EmergencyHandler()

                if event.key == pygame.K_3:
                    intersection = Intersection()
                    algo_name    = 'dp'
                    controller   = make_controller(algo_name, intersection)
                    emergency    = EmergencyHandler()

                # profile switching
                if event.key == pygame.K_p:
                    profile_index = (profile_index + 1) % len(PROFILE_NAMES)
                    spawner.set_profile(PROFILE_NAMES[profile_index])

                # emergency spawn
                if event.key == pygame.K_e:
                    if not emergency.active:
                        lane = random.choice(LANE_NAMES)
                        ev   = Vehicle('emergency', lane)
                        intersection.add_vehicle(ev)
                        emergency.trigger(lane, intersection)

        spawner.update(dt, intersection)

        if emergency.active:
            cleared = emergency.update(dt, intersection)
            if cleared:
                controller.start(intersection)
        else:
            controller.update(dt, intersection)

        intersection.update_clearing(dt)
        renderer.draw(intersection, controller, algo_name, emergency, spawner.profile_name)
        pygame.display.flip()

if __name__ == "__main__":
    main()