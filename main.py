# main.py
import pygame
import sys
import random

from config     import SCREEN_WIDTH, SCREEN_HEIGHT, LANE_NAMES, LANE_WIDTH
from core       import Intersection, Vehicle
from algorithms import FixedCycleController, GreedyController, DPController
from ui         import Renderer
from ui.vehicle_animator import VehicleAnimator
from profiles   import VehicleSpawner, PROFILES
from emergency  import EmergencyHandler
from server     import OptimizerClient

VEHICLE_COLORS = {
    'two_wheeler':  ( 50, 180, 255),
    'four_wheeler': ( 50, 220, 130),
    'heavy':        (255, 150,  50),
    'emergency':    (255,  50,  80),
}

PROFILE_NAMES = list(PROFILES.keys())

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

    # start windowed, toggle fullscreen with F
    flags        = 0
    screen       = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), flags)
    fullscreen   = False
    pygame.display.set_caption("Traffic Signal Optimizer")
    clock        = pygame.time.Clock()

    intersection = Intersection()
    algo_name    = 'fixed'
    controller   = make_controller(algo_name, intersection)
    renderer     = Renderer(screen)
    spawner      = VehicleSpawner(profile_name='morning')
    emergency    = EmergencyHandler()
    animator     = VehicleAnimator()
    profile_index = 0
    client       = OptimizerClient()

    def on_server_decision(result):
        print(f"[Server] {result['reason']} → {result['next_lane']} for {result['green_time']}s")
        controller.apply_server_decision(result, intersection)

    while True:
        dt        = clock.tick(60) / 1000.0
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    intersection = Intersection()
                    algo_name    = 'fixed'
                    controller   = make_controller(algo_name, intersection)
                    emergency    = EmergencyHandler()
                    animator     = VehicleAnimator()

                if event.key == pygame.K_2:
                    intersection = Intersection()
                    algo_name    = 'greedy'
                    controller   = make_controller(algo_name, intersection)
                    emergency    = EmergencyHandler()
                    animator     = VehicleAnimator()

                if event.key == pygame.K_3:
                    intersection = Intersection()
                    algo_name    = 'dp'
                    controller   = make_controller(algo_name, intersection)
                    emergency    = EmergencyHandler()
                    animator     = VehicleAnimator()

                if event.key == pygame.K_p:
                    profile_index = (profile_index + 1) % len(PROFILE_NAMES)
                    spawner.set_profile(PROFILE_NAMES[profile_index])

                if event.key == pygame.K_e:
                    if not emergency.active:
                        lane = random.choice(LANE_NAMES)
                        ev   = Vehicle('emergency', lane,
                                    'left' if 'Left' in lane else 'straight')
                        intersection.add_vehicle(ev)
                        emergency.trigger(lane, intersection)
                        # greedy and dp interrupt immediately
                        if algo_name in ('greedy', 'dp'):
                            controller.emergency_interrupt(lane, intersection)  

                if event.key == pygame.K_f:
                    fullscreen = not fullscreen
                    if fullscreen:
                        screen = pygame.display.set_mode(
                            (0, 0), pygame.FULLSCREEN)
                    else:
                        screen = pygame.display.set_mode(
                            (SCREEN_WIDTH, SCREEN_HEIGHT))
                    renderer = Renderer(screen)

        spawner.update(dt, intersection)

        if emergency.active:
            cleared = emergency.update(dt, intersection)
            if cleared:
                client.request_decision(
                    intersection, algo_name,
                    0, 0,
                    on_server_decision
                )
                controller.start(intersection)
        else:
            controller.update(dt, intersection)

        # set yellow arms for renderer
        intersection._yellow_arms = set()
        if hasattr(controller, 'yellow_phase') and controller.yellow_phase:
            if controller.current_group:
                for lane in controller.current_group:
                    arm = lane.replace('-Left','').replace('-Right','')
                    intersection._yellow_arms.add(arm)

        # get cleared vehicles and spawn crossing animations
        cleared_vehicles = intersection.update_clearing(dt)
        for v in cleared_vehicles:
            color = VEHICLE_COLORS.get(v.type, (255, 255, 255))
            animator.spawn(v, renderer.cx, renderer.cy, LANE_WIDTH, color)

        animator.update(dt)

        renderer.draw(
            intersection, controller, algo_name,
            emergency, spawner.profile_name,
            mouse_pos, animator
        )
        pygame.display.flip()

if __name__ == "__main__":
    main()