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
        depth = max(0, min(1, 1 - (z / max_z)))

        # perspective curve (same idea as your road)
        p = depth * depth

        y = horizon_y + (bottom - horizon_y) * p
        scale = 0.2 + p * 1.8

        return y, scale

    def update(self, dt, playerLane, playerIsJumping):

        # spawn logic
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = random.uniform(0.5, 1.5)
            self.spawn()

        for o in self.entities:

            if o.get("collected", False):
                continue

            o["z"] -= self.speed * dt

            # collision
            if abs(o["z"]) < 50 and o["lane"] == playerLane:

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
        self.entities = [o for o in self.entities if o["z"] > -200]

    def draw(self, screen):

        for o in sorted(self.entities, key=lambda e: e["z"], reverse=True):

            x = self.get_lane_x(o["lane"])
            y, scale = self.project(o["z"])

            if o["type"] == "train":

                w = 80 * scale
                h = 100 * scale
                rect = Rect(x - w / 2, y - h, w, h)

                screen.draw.filled_rect(rect, (0, 0, 255))

            elif o["type"] == "barrier":

                w = 60 * scale
                h = 40 * scale
                rect = Rect(x - w / 2, y - h, w, h)

                screen.draw.filled_rect(rect, (255, 165, 0))

            elif o["type"] == "coin" and not o["collected"]:

                r = 15 * scale
                screen.draw.filled_circle((x, y - r), r, (255, 215, 0))

    def get_lane_x(self, lane):
        lane_width = 80
        return (self.WIDTH / 2) + (lane - 1) * lane_width