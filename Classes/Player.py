import pygame
from pygame import Rect
from Classes.AnimationManager import AnimationManager


class Player:

    def __init__(self, HEIGHT, WIDTH):
        self.HEIGHT = HEIGHT
        self.WIDTH = WIDTH

        self.player_width = WIDTH * 0.04
        self.player_height = self.player_width * 1.5

        self.current_lane = 1
        self._visual_lane = 1.0   # float, lerps toward current_lane for smooth movement
        self.y_offset = 0
        self.y_velocity = 0
        self.gravity = -2.5
        self.jump_power = 38
        self.is_Jumping = False
        self.jumps_remaining = 2  # double-jump: 2 jumps per grounded state
        self.base_y = HEIGHT * 0.87

        # max jump height for shadow ratio
        self._max_jump_h = (self.jump_power ** 2) / (2 * abs(self.gravity))  # ~300px

        # hit flash
        self.hit_timer = 0.0
        self.hit_duration = 0.5  # seconds of red tint after being hit

        # Squash-and-stretch scale factors
        self._scale_x = 1.0
        self._scale_y = 1.0
        self._land_squash = 0.0   # 0-1 timer for landing squash

        self.anim_manager = AnimationManager("images/Character3SpriteSheet.png", 4)

    def move_left(self):
        if self.current_lane > 0:
            self.current_lane -= 1

    def move_right(self):
        if self.current_lane < 2:
            self.current_lane += 1

    def jump(self):
        if self.jumps_remaining > 0:
            self.is_Jumping = True
            self.y_velocity = self.jump_power
            self.jumps_remaining -= 1
            self._land_squash = 0.0   # cancel any residual landing squash

    def trigger_hit(self):
        self.hit_timer = self.hit_duration

    def update(self, dt=1/60):
        self.anim_manager.update(dt)
        # Smooth lane slide — frame-rate independent lerp
        _t = 1.0 - (0.72 ** (dt * 60))
        self._visual_lane += (self.current_lane - self._visual_lane) * _t

        if self.hit_timer > 0:
            self.hit_timer -= 1 / 60

        # ── Squash & stretch ─────────────────────────────────────────────────
        if self.is_Jumping:
            t = self.y_velocity / self.jump_power   # +1 = just launched, -1 = max fall
            if t > 0:   # rising — stretch tall
                sy = 1.0 + t * 0.30
                sx = 1.0 / sy * 0.90 + 0.10
            else:       # falling — slight compress
                sy = max(0.88, 1.0 + t * 0.12)
                sx = 1.0
            self._scale_x = sx
            self._scale_y = sy
        else:
            # Landing squash: briefly squish horizontally
            if self._land_squash > 0:
                self._land_squash = max(0.0, self._land_squash - dt / 0.12)
                k = self._land_squash
                self._scale_x = 1.0 + k * 0.25
                self._scale_y = 1.0 - k * 0.18
            else:
                self._scale_x = 1.0
                self._scale_y = 1.0

        if self.is_Jumping:
            scale = dt * 60   # normalise to 60 fps so values stay intuitive
            self.y_offset  += self.y_velocity * scale
            self.y_velocity += self.gravity   * scale

            if self.y_offset <= 0:
                self.y_offset = 0
                self.is_Jumping = False
                self.y_velocity = 0
                self.jumps_remaining = 2  # reset on landing
                self._land_squash = 1.0   # trigger landing squash

    def _get_draw_x(self):
        center_x      = self.WIDTH / 2
        horizon_y     = self.HEIGHT * 0.4
        road_bottom_w = self.WIDTH * 0.6
        road_top_w    = self.WIDTH * 0.1
        depth         = (self.base_y - horizon_y) / (self.HEIGHT - horizon_y)
        current_road_w = road_top_w + (road_bottom_w - road_top_w) * depth
        lane_width    = current_road_w / 3
        # Use _visual_lane (smooth float) instead of integer current_lane
        return center_x + (self._visual_lane - 1) * lane_width

    def get_screen_x(self):
        return self._get_draw_x()

    def draw(self, screen):
        draw_x = self._get_draw_x()
        draw_y = self.base_y - self.y_offset

        # --- Shadow on the ground ---
        ratio = max(0.15, 1.0 - self.y_offset / self._max_jump_h)
        shadow_w = max(8, int(self.player_width * 1.4 * ratio))
        shadow_h = max(3, int(shadow_w * 0.22))
        shadow_alpha = int(140 * ratio)

        shadow_surf = pygame.Surface((shadow_w, shadow_h), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, shadow_alpha), (0, 0, shadow_w, shadow_h))
        screen.surface.blit(shadow_surf, (int(draw_x - shadow_w / 2), int(self.base_y - shadow_h // 2)))

        # --- Sprite (with squash & stretch) ---
        frame = self.anim_manager.get_current_image()
        sw = int(self.player_width  * 1.5 * self._scale_x)
        sh = int(self.player_height * 1.5 * self._scale_y)
        scaled_frame = pygame.transform.scale(frame, (max(1, sw), max(1, sh)))

        # Red tint when hit (adds to red channel only; keeps transparency intact)
        if self.hit_timer > 0:
            tinted = scaled_frame.copy()
            strength = int(160 * (self.hit_timer / self.hit_duration))
            overlay = pygame.Surface(tinted.get_size(), pygame.SRCALPHA)
            overlay.fill((strength, 0, 0, 0))
            tinted.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
            scaled_frame = tinted

        frame_rect = scaled_frame.get_rect()
        frame_rect.centerx = int(draw_x)
        frame_rect.bottom = int(draw_y)

        screen.surface.blit(scaled_frame, frame_rect.topleft)

    def getLane(self):
        return self.current_lane

    def getIsJumping(self):
        return self.is_Jumping

    def reset(self):
        self.current_lane  = 1
        self._visual_lane  = 1.0
        self.y_offset      = 0
        self.y_velocity    = 0
        self.is_Jumping    = False
        self.jumps_remaining = 2
        self.hit_timer     = 0.0
        self._scale_x      = 1.0
        self._scale_y      = 1.0
        self._land_squash  = 0.0
