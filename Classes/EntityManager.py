import pygame
import random
import math
from pygame import Rect


class EntityManager:

    def __init__(self, HEIGHT, WIDTH):
        self.entities = []
        self.HEIGHT = HEIGHT
        self.WIDTH = WIDTH

        self.spawn_timer = 1.0
        self.speed = 500
        self.time = 0.0

        # Load coin image (nearest-neighbor scale for pixel feel)
        try:
            raw_coin = pygame.image.load("images/coin.png").convert_alpha()
            self._coin_base = raw_coin  # keep original for runtime scaling
        except Exception:
            self._coin_base = None

        # Load boost_key image
        try:
            raw_boost = pygame.image.load("images/boost_key.gif").convert_alpha()
            self._boost_base = raw_boost
        except Exception:
            self._boost_base = None

        # Load obstacle rock images
        try:
            raw_train = pygame.image.load("images/Obstacles/double_jump_rock.png").convert_alpha()
            self._train_img    = raw_train
            self._train_aspect = raw_train.get_width() / max(1, raw_train.get_height())
        except Exception:
            self._train_img    = None
            self._train_aspect = 0.75

        try:
            raw_barrier = pygame.image.load("images/Obstacles/simple_jump_rock.png").convert_alpha()
            self._barrier_img    = raw_barrier
            self._barrier_aspect = raw_barrier.get_width() / max(1, raw_barrier.get_height())
        except Exception:
            self._barrier_img    = None
            self._barrier_aspect = 1.67

    def reset(self):
        self.entities = []
        self.spawn_timer = 1.0
        self.time = 0.0

    def spawn(self):
        lane = random.choice([0, 1, 2])
        # boost_key is rarer; coins are most common
        obstacle_type = random.choices(
            ["barrier", "train", "coin", "coin", "boost_key"],
            weights=[22, 17, 38, 20, 3]
        )[0]

        entity = {
            "type": obstacle_type,
            "lane": lane,
            "z": 3000,
            "collected": False,
            "phase": random.uniform(0, math.pi * 2),  # for coin spin animation
        }
        self.entities.append(entity)

    def project(self, z):
        horizon_y = self.HEIGHT * 0.4
        bottom = self.HEIGHT
        max_z = 3000
        depth = max(0, 1 - (z / max_z))
        p = depth * depth
        y = horizon_y + (bottom - horizon_y) * p
        scale = 0.2 + p * 1.8
        return y, scale, p

    def update(self, dt, playerLane, playerIsJumping, ground_speed, playerIsInvincible=False):
        self.speed = (3000 / 15) * (ground_speed / dt)
        self.time += dt

        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_timer = random.uniform(0.5, 1.5)
            self.spawn()

        for o in self.entities:
            if o.get("collected", False):
                continue

            o["z"] -= self.speed * dt

            if abs(o["z"] - 345) < 70 and o["lane"] == playerLane:

                if o["type"] == "coin":
                    o["collected"] = True
                    return "coin"

                elif o["type"] == "boost_key":
                    o["collected"] = True
                    return "boost"

                elif not playerIsInvincible:
                    # both train and barrier are avoidable by jumping
                    if o["type"] in ("train", "barrier"):
                        if not playerIsJumping:
                            o["collected"] = True
                            return "dead"

        self.cleanup()

    def cleanup(self):
        self.entities = [o for o in self.entities if o["z"] > -500]

    # ---- Drawing ----

    def draw_bg(self, screen, player_z):
        filtered = [e for e in self.entities if e["z"] > player_z]
        self._draw_entities(screen, filtered)

    def draw_fg(self, screen, player_z):
        filtered = [e for e in self.entities if e["z"] <= player_z]
        self._draw_entities(screen, filtered)

    def _draw_shadow(self, screen, cx, ground_y, w):
        sw = int(w * 0.85)
        sh = max(4, int(sw * 0.18))
        alpha = 90
        surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
        pygame.draw.ellipse(surf, (0, 0, 0, alpha), (0, 0, sw, sh))
        screen.surface.blit(surf, (int(cx - sw / 2), int(ground_y - sh // 2)))

    def _draw_entities(self, screen, entity_list):
        for o in sorted(entity_list, key=lambda e: e["z"], reverse=True):
            if o.get("collected", False):
                continue

            y, scale, p = self.project(o["z"])
            x = self.get_lane_x(o["lane"], p)

            if o["type"] == "train":
                # Base size: height ~140 at scale=1, width from image aspect
                base_h = int(140 * scale)
                base_w = int(base_h * self._train_aspect)
                gnd_y  = int(y)

                self._draw_shadow(screen, x, gnd_y, base_w)

                if self._train_img is not None:
                    scaled = pygame.transform.scale(self._train_img, (base_w, base_h))
                    screen.surface.blit(scaled, (int(x - base_w / 2), gnd_y - base_h))
                else:
                    # Fallback rectangle
                    pygame.draw.rect(screen.surface, (30, 100, 220),
                                     (int(x - base_w / 2), gnd_y - base_h, base_w, base_h))

            elif o["type"] == "barrier":
                # Base size: height ~65 at scale=1, width from image aspect
                base_h = int(65 * scale)
                base_w = int(base_h * self._barrier_aspect)
                gnd_y  = int(y)

                self._draw_shadow(screen, x, gnd_y, base_w)

                if self._barrier_img is not None:
                    scaled = pygame.transform.scale(self._barrier_img, (base_w, base_h))
                    screen.surface.blit(scaled, (int(x - base_w / 2), gnd_y - base_h))
                else:
                    # Fallback rectangle
                    pygame.draw.rect(screen.surface, (255, 145, 0),
                                     (int(x - base_w / 2), gnd_y - base_h, base_w, base_h))

            elif o["type"] == "coin":
                r = max(15, int(54 * scale))
                gnd_y = int(y)
                cx_i = int(x)

                # Coin spin: vary width with sin
                spin = abs(math.sin(self.time * 4.0 + o["phase"]))
                draw_w = max(3, int(r * 2 * spin))
                draw_h = r * 2

                if self._coin_base is not None:
                    coin_scaled = pygame.transform.scale(self._coin_base, (draw_w, draw_h))
                    screen.surface.blit(coin_scaled, (cx_i - draw_w // 2, gnd_y - r - draw_h // 2))
                else:
                    # Fallback drawn coin
                    pygame.draw.ellipse(screen.surface, (255, 215, 0),
                                        (cx_i - draw_w // 2, gnd_y - r - draw_h // 2, draw_w, draw_h))

                # Shadow
                self._draw_shadow(screen, cx_i, gnd_y, r * 2)

            elif o["type"] == "boost_key":
                bw = max(8, int(50 * scale))
                bh = max(8, int(50 * scale))
                gnd_y = int(y)
                cx_i = int(x)

                # Gentle float bob
                bob = int(math.sin(self.time * 3.0 + o["phase"]) * max(2, int(6 * scale)))

                # Shadow (smaller as it floats)
                self._draw_shadow(screen, cx_i, gnd_y, bw)

                if self._boost_base is not None:
                    boost_scaled = pygame.transform.scale(self._boost_base, (bw, bh))
                    screen.surface.blit(boost_scaled, (cx_i - bw // 2, gnd_y - bh + bob))
                else:
                    # Fallback: bright purple key shape
                    pygame.draw.rect(screen.surface, (200, 50, 255),
                                     (cx_i - bw // 2, gnd_y - bh + bob, bw, bh))
                    pygame.draw.rect(screen.surface, (230, 130, 255),
                                     (cx_i - bw // 2 + 3, gnd_y - bh + bob + 3, bw - 6, bh - 6))

    def get_lane_x(self, lane, p):
        center_x = self.WIDTH / 2
        road_bottom_w = self.WIDTH * 0.6
        road_top_w = self.WIDTH * 0.1
        current_road_w = road_top_w + (road_bottom_w - road_top_w) * p
        lane_width = current_road_w / 3
        return center_x + (lane - 1) * lane_width
