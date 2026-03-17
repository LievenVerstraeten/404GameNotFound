# create player movement here
# have an animation in here

import pygame
from pygame import Rect


class Player:

    def __init__(self, HEIGHT, WIDTH):
        # screen variables:
        self.HEIGHT = HEIGHT
        self.WIDTH = WIDTH

        # player looks:
        self.player_width = WIDTH * 0.04
        self.player_height = self.player_width * 1.5
        self.tshirt = (255, 0, 0)
        self.skin = (255, 200, 200)

        # positioning
        self.current_lane = 1  # 0 for left, 1 for middle and 2 for right
        self.y_offset = 0  # current height
        self.y_velocity = 0  # current vertical speed
        self.gravity = -1.5
        self.jump_power = 30
        self.is_Jumping = False  # no double jump check
        self.base_y = HEIGHT * 0.87


    def move_left(self):
        if self.current_lane > 0:
            self.current_lane -= 1

    def move_right(self):
        if self.current_lane < 2:
            self.current_lane += 1

    def jump(self):
        if not self.is_Jumping:
            self.is_Jumping = True
            self.y_velocity = self.jump_power


    def update(self):
        # gravity when jumping
        if self.is_Jumping:
            self.y_offset += self.y_velocity
            self.y_velocity += self.gravity

            # reset when landed
            if self.y_offset <= 0:
                self.y_offset = 0
                self.is_Jumping = False
                self.y_velocity = 0


    def draw(self, screen):
        # center_x = self.WIDTH / 2
        #
        # # temp variables
        # horizon_y = self.HEIGHT * 0.4
        # road_bottom_width = self.WIDTH * 0.6
        # road_top_width = self.WIDTH * 0.1
        #
        # depth = (self.base_y - horizon_y) / (self.HEIGHT - horizon_y)
        # current_road_width = road_top_width + (road_bottom_width - road_top_width) * depth
        #
        # # lane width and positions
        # lane_width = current_road_width / 3
        # lane_positions = [
        #     center_x - lane_width,
        #     center_x,
        #     center_x + lane_width
        # ]
        #
        # # Get our exact X depending on the lane we are in
        # draw_x = lane_positions[self.current_lane]
        #
        # # Our Y position is the base_y minus any jump offset
        # draw_y = self.base_y - self.y_offset
        #
        # # Draw the body (Rectangle)
        # # Center the rectangle horizontally on draw_x, and sit the bottom on draw_y
        # body_rect = Rect(draw_x - (self.player_width / 2), draw_y - self.player_height, self.player_width, self.player_height)
        # screen.draw.filled_rect(body_rect, self.tshirt)
        #
        # # Draw the head (Circle) on top of the body
        # head_radius = self.player_width / 1.5
        # head_y = draw_y - self.player_height - (head_radius * 0.5)
        #
        # # Pygame zero's filled_circle takes an (x,y) tuple for center and a radius
        # screen.draw.filled_circle((draw_x, head_y), head_radius, self.skin)

        # Define the exact X position for each of the 3 lanes
        # The center lane is the exact middle of the screen
        center_x = self.WIDTH / 2

        # We need to know the width of the road at the player's base_y.
        # Since base_y is heavily towards the bottom, the road is wide here.
        horizon_y = self.HEIGHT * 0.4
        road_bottom_w = self.WIDTH * 0.6
        road_top_w = self.WIDTH * 0.1

        # Calculate how far down the screen the player is (percentage)
        depth = (self.base_y - horizon_y) / (self.HEIGHT - horizon_y)
        current_road_w = road_top_w + (road_bottom_w - road_top_w) * depth

        # Calculate lane positions
        lane_width = current_road_w / 3
        # Left lane center, Middle lane center, Right lane center
        lane_positions = [
            center_x - lane_width,
            center_x,
            center_x + lane_width
        ]

        # Get our exact X depending on the lane we are in
        draw_x = lane_positions[self.current_lane]

        # Our Y position is the base_y minus any jump offset
        draw_y = self.base_y - self.y_offset

        # Draw the body (Rectangle)
        # Center the rectangle horizontally on draw_x, and sit the bottom on draw_y
        body_rect = Rect(draw_x - (self.player_width / 2), draw_y - self.player_height, self.player_width, self.player_height)
        screen.draw.filled_rect(body_rect, self.tshirt)

        # Draw the head (Circle) on top of the body
        head_radius = self.player_width / 1.5
        head_y = draw_y - self.player_height - (head_radius * 0.5)

        # Pygame zero's filled_circle takes an (x,y) tuple for center and a radius
        screen.draw.filled_circle((draw_x, head_y), head_radius, self.skin)


    def getLane (self):
        return self.current_lane
    def getIsJumping (self):
        return self.is_Jumping

    def reset(self):
        self.current_lane = 1
        self.y_offset = 0
        self.y_velocity = 0
        self.is_Jumping = False










