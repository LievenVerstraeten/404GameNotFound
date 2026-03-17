import pygame
import random
from pygame import Rect


class EntityManager:

    def __init__(self, HEIGHT, WIDTH):
        self.entities = []
        self.HEIGHT = HEIGHT
        self.WIDTH = WIDTH

        self.spawn_timer = 1.0
        self.speed = 500

    def reset(self):
        self.entities = []
        self.spawn_timer = 1.0

    def spawn(self):
        lane = random.choice([0, 1, 2])
        obstacle_type = random.choice(["barrier", "train", "coin"])

        entity = {
            "type": obstacle_type,
            "lane": lane,
            "z": 3000,
            "collected": False
        }

        self.entities.append(entity)

    # helper function for the depth
    def project(self, z):
        horizon_y = self.HEIGHT * 0.4
        bottom = self.HEIGHT

        # normalize distance
        max_z = 3000
        depth = max(0, 1 - (z / max_z))

        # perspective curve (same idea as your road)
        p = depth * depth

        y = horizon_y + (bottom - horizon_y) * p
        scale = 0.2 + p * 1.8

        return y, scale, p

    def update(self, dt, playerLane, playerIsJumping, ground_speed):
        # Ground moves 3000 Z units every 15 full segments.
        # So ground speed in Z units per frame = (3000 / 15) * (ground_speed / dt).
        self.speed = (3000 / 15) * (ground_speed / dt)

        # spawn logic
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = random.uniform(0.5, 1.5)
            self.spawn()

        for o in self.entities:

            if o.get("collected", False):
                continue

            o["z"] -= self.speed * dt

            # collision - player depth is approx z=345 based on base_y Math
            if abs(o["z"] - 345) < 70 and o["lane"] == playerLane:

                if o["type"] == "train":
                    return True

                elif o["type"] == "barrier":
                    if not playerIsJumping:
                        return True

                elif o["type"] == "coin":
                    o["collected"] = True
                    return False

        self.cleanup()

    def cleanup(self):
        self.entities = [o for o in self.entities if o["z"] > -500]

    def draw_bg(self, screen, player_z):
        filtered_entities = [e for e in self.entities if e["z"] > player_z]
        self._draw_entities(screen, filtered_entities)

    def draw_fg(self, screen, player_z):
        filtered_entities = [e for e in self.entities if e["z"] <= player_z]
        self._draw_entities(screen, filtered_entities)

    def _draw_entities(self, screen, entity_list):
        for o in sorted(entity_list, key=lambda e: e["z"], reverse=True):

            y, scale, p = self.project(o["z"])
            x = self.get_lane_x(o["lane"], p)

            if o["type"] == "train":

                w = 120 * scale
                h = 160 * scale
                rect = Rect(x - w / 2, y - h, w, h)

                screen.draw.filled_rect(rect, (0, 0, 255))

            elif o["type"] == "barrier":

                w = 100 * scale
                h = 60 * scale
                rect = Rect(x - w / 2, y - h, w, h)

                screen.draw.filled_rect(rect, (255, 165, 0))

            elif o["type"] == "coin" and not o["collected"]:

                r = 20 * scale
                screen.draw.filled_circle((x, y - r), r, (255, 215, 0))

    def get_lane_x(self, lane, p):
        center_x = self.WIDTH / 2

        road_bottom_w = self.WIDTH * 0.6
        road_top_w = self.WIDTH * 0.1

        current_road_w = road_top_w + (road_bottom_w - road_top_w) * p
        lane_width = current_road_w / 3

        return center_x + (lane - 1) * lane_width