import os
import pygame
import math
import random

# getting the monitor information
from screeninfo import get_monitors

# importing the classes
from Classes.Background import Background
from Classes.Player import Player
from Classes.EntityManager import EntityManager

# Screen information:
x = 0
y = 30
os.environ['SDL_VIDEO_WINDOW_POS'] = f'{x},{y}'  # setting the screen to the top right.
import pgzrun

WIDTH = get_monitors()[0].width
HEIGHT = get_monitors()[0].height - y
TITLE = "404GameNotFound"

# Constants:
MOVE_OFFSET = 0
SPEED = 0.05

# Classes:
road = Background(HEIGHT, WIDTH)
player = Player(HEIGHT, WIDTH)
entityManager = EntityManager(HEIGHT, WIDTH)

# global variables
gameLoop = True
score = 0
high_scores = []


def on_key_down(key):
    # Pygame Zero handles input via these event functions easily
    if key == keys.LEFT and gameLoop:
        player.move_left()
    elif key == keys.RIGHT and gameLoop:
        player.move_right()
    elif key == keys.SPACE:
        if not gameLoop:
            reset()
        else:
            player.jump()


def update():
    # How we move our camera forward to imitate 3D movement
    global MOVE_OFFSET
    global gameLoop
    global score
    if gameLoop:
        MOVE_OFFSET += SPEED
        if MOVE_OFFSET >= 1.0:
            MOVE_OFFSET -= 1.0

        road.update(MOVE_OFFSET)
        player.update()

        result = entityManager.update(1 / 60, player.getLane(), player.getIsJumping(), SPEED)
        if result:
            gameLoop = False
            high_scores.append(score)
            high_scores.sort(reverse=True)
            if len(high_scores) > 5:
                high_scores.pop()
        elif not result:
            score += 10


def draw():
    screen.clear()  # resetting what is on the screen so you don't see the previous frame
    road.draw(screen)  # drawing the road and the background (has to be done first)
    entityManager.draw_bg(screen, 345)
    player.draw(screen)
    entityManager.draw_fg(screen, 345)

    if gameLoop:
        screen.draw.text(f"Score: {score}", topleft=(20, 20), fontsize=40, color="white")
    else:
        screen.draw.text("GAME OVER", center=(WIDTH // 2, HEIGHT // 2 - 100), fontsize=80, color="red")
        screen.draw.text("Press SPACE to restart", center=(WIDTH // 2, HEIGHT // 2 - 20), fontsize=40, color="white")

        # Draw high scores
        screen.draw.text("High Scores:", center=(WIDTH // 2, HEIGHT // 2 + 30), fontsize=35, color="yellow")
        for i, s in enumerate(high_scores):
            screen.draw.text(f"{i + 1}. {s}", center=(WIDTH // 2, HEIGHT // 2 + 70 + i * 30), fontsize=30,
                             color="white")


def reset():
    global MOVE_OFFSET
    global score
    global gameLoop
    MOVE_OFFSET = 0
    score = 0
    gameLoop = True
    entityManager.reset()
    player.reset()


pgzrun.go()
