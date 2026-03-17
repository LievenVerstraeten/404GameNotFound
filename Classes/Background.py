import pygame
from pygame import Rect

# Colors:
SKYBLUE = (135, 206, 235)
GRASS = (34, 139, 34)
TRACK_COLORS = [(120, 120, 120), (100, 100, 100)]  # Dark gray and light gray


class Background:
    def __init__(self, HEIGHT, WIDTH):
        self.HEIGHT = HEIGHT
        self.WIDTH = WIDTH
        self.move_offset = 0
        self.absolute_offset = 0
        self.prev_offset = 0

    def update(self, new_offset):
        # Detect wrap-around to increment our absolute color offset
        if new_offset < self.prev_offset:
            self.absolute_offset += 1
        self.prev_offset = new_offset
        self.move_offset = new_offset

    def draw(self, screen):
        # Road Variables:
        horizon_y = self.HEIGHT * 0.4
        road_top_w = self.WIDTH * 0.1  # Narrow road at the horizon
        road_bottom_w = self.WIDTH * 0.6  # Wide road at the bottom of the screen
        center_x = self.WIDTH / 2

        # Drawing the background:
        sky_rect = Rect(0, 0, self.WIDTH, horizon_y)
        screen.draw.filled_rect(sky_rect, SKYBLUE)

        grass_rect = Rect(0, horizon_y, self.WIDTH, self.HEIGHT * 0.6)
        screen.draw.filled_rect(grass_rect, GRASS)

        # Draw alternating road segments
        segments = 15
        for i in range(segments):
            # Calculate depth (0.0 at horizon, 1.0 at bottom of screen)
            depth_start = (i + self.move_offset) / segments
            depth_end = (i + 1 + self.move_offset) / segments

            # Don't draw past the camera
            if depth_start >= 1.0:
                continue
            if depth_end > 1.0:
                depth_end = 1.0

            # Perspective mapping (squaring the depth)
            p_start = depth_start * depth_start
            p_end = depth_end * depth_end

            # Y coordinates on screen
            y1 = horizon_y + (self.HEIGHT - horizon_y) * p_start
            y2 = horizon_y + (self.HEIGHT - horizon_y) * p_end

            # Road widths at these Y coordinates
            w1 = road_top_w + (road_bottom_w - road_top_w) * p_start
            w2 = road_top_w + (road_bottom_w - road_top_w) * p_end

            # Polygon points
            pts = [
                (center_x - w1 / 2, y1),  # Top left
                (center_x + w1 / 2, y1),  # Top right
                (center_x + w2 / 2, y2),  # Bottom right
                (center_x - w2 / 2, y2),  # Bottom left
            ]

            # Alternate colors seamlessly based on index and the wrap-around offset
            color_idx = (i + self.absolute_offset) % 2
            pygame.draw.polygon(screen.surface, TRACK_COLORS[color_idx], pts)

        # Draw lane dividers (vertical lines)
        pygame.draw.line(screen.surface, (255, 255, 255),
                         (center_x - road_top_w / 6, horizon_y),
                         (center_x - road_bottom_w / 6, self.HEIGHT), 3)  # Left divider
        pygame.draw.line(screen.surface, (255, 255, 255),
                         (center_x + road_top_w / 6, horizon_y),
                         (center_x + road_bottom_w / 6, self.HEIGHT), 3)  # Right divider