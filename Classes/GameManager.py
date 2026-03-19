import pygame
import sys
from Classes.Background import Background
from Classes.Player import Player
from Classes.EntityManager import EntityManager
from Classes.Boss import Boss
from Classes.HeadController import HeadController

class GameManager:
    def __init__(self, width, height, settings):
        self.width = width
        self.height = height
        self.settings = settings
        
        self.road = Background(height, width)
        self.player = Player(height, width)
        self.entityManager = EntityManager(height, width)
        self.boss = Boss(height, width)
        self.head_ctrl = HeadController()
        
        self.game_state = "menu"
        self.move_offset = 0.0
        self.speed = settings.BASE_SPEED
        self.score = 0
        self.high_scores = []
        self.lives = settings.MAX_LIVES
        self.invincible_timer = 0.0
        self.boost_active = False
        self.boost_timer = 0.0
        self.score_multiplier = 1
        self.collected_coins = 0
        self.coin_boost_active = False
        self.coin_boost_timer = 0.0
        self.game_time = 0.0
        
        self.floaters = []
        self.hit_flash_timer = 0.0

    def start_game(self):
        self.reset()

    def reset(self):
        self.move_offset = 0.0
        self.score = 0
        self.game_state = "playing"
        self.lives = self.settings.MAX_LIVES
        self.collected_coins = 0
        self.invincible_timer = 0.0
        self.game_time = 0.0
        self.boost_active = False
        self.boost_timer = 0.0
        self.score_multiplier = 1
        self.coin_boost_active = False
        self.coin_boost_timer = 0.0
        self.hit_flash_timer = 0.0
        self.floaters.clear()
        self.entityManager.reset()
        self.player.reset()
        self.boss.reset()

    def on_key_down(self, key):
        if key == pygame.K_ESCAPE:
            if self.game_state in ("tutorial", "settings", "playing", "game_over"):
                self.game_state = "menu"
            elif self.game_state == "menu":
                sys.exit(0)
            return

        if key == pygame.K_SPACE:
            if self.game_state == "menu":
                self.start_game()
            elif self.game_state in ("tutorial", "settings"):
                self.game_state = "menu"
            elif self.game_state == "playing":
                self.player.jump()
            elif self.game_state == "game_over":
                self.reset()
            return

        if self.game_state != "playing":
            return

        if key in (pygame.K_LEFT, pygame.K_a):
            self.player.move_left()
        elif key in (pygame.K_RIGHT, pygame.K_d):
            self.player.move_right()
        elif key in (pygame.K_UP, pygame.K_w):
            if self.collected_coins >= self.settings.COIN_BOOST_COST and not self.coin_boost_active:
                self.collected_coins -= self.settings.COIN_BOOST_COST
                self.coin_boost_active = True
                self.coin_boost_timer = self.settings.COIN_BOOST_DURATION
                self.floaters.append({'text': 'SPEED  x2 !', 'color': (80, 210, 255),
                                   'x': self.width // 2, 'y': int(self.height * 0.44), 'timer': 1.4})

        elif key in (pygame.K_DOWN, pygame.K_s):
            if self.boss.active and not self.boss.defeated and self.collected_coins > 0:
                self.collected_coins -= 1
                speed_mult = 2.0 if self.coin_boost_active else 1.0
                self.boss.fire_player_shot(self.player.getLane(), speed_mult)

    def update(self, dt):
        self.speed = self.settings.BASE_SPEED * (2.0 if self.coin_boost_active else 1.0)
        self.move_offset += self.speed * dt * 60
        if self.move_offset >= 1.0:
            self.move_offset -= 1.0
        self.road.update(self.move_offset, dt, self.speed)

        for f in self.floaters:
            f['y'] -= 60 * dt
            f['timer'] -= dt
        self.floaters[:] = [f for f in self.floaters if f['timer'] > 0]

        if self.game_state != "playing":
            return

        self.player.update(dt)

        if self.invincible_timer > 0:
            self.invincible_timer -= dt
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= dt
        if self.boost_active:
            self.boost_timer -= dt
            if self.boost_timer <= 0:
                self.boost_active = False; self.boost_timer = 0.0; self.score_multiplier = 1
        if self.coin_boost_active:
            self.coin_boost_timer -= dt
            if self.coin_boost_timer <= 0:
                self.coin_boost_active = False; self.coin_boost_timer = 0.0

        if self.head_ctrl.enabled:
            d = self.head_ctrl.consume_lane_change()
            if d == -1: self.player.move_left()
            elif d == 1: self.player.move_right()
            while self.head_ctrl.consume_jump():
                self.player.jump()
            if self.head_ctrl.consume_shoot() and self.boss.active and not self.boss.defeated and self.collected_coins > 0:
                self.collected_coins -= 1
                self.boss.fire_player_shot(self.player.getLane(),
                                      2.0 if self.coin_boost_active else 1.0)

        result = self.entityManager.update(
            dt, self.player.getLane(), self.player.getIsJumping(), self.speed, self.invincible_timer > 0)

        if result == "dead":
            self.lives -= 1
            self.invincible_timer = self.settings.INVINCIBLE_DURATION
            self.hit_flash_timer = self.settings.INVINCIBLE_DURATION * 0.55
            self.player.trigger_hit()
            if self.lives <= 0:
                self.game_state = "game_over"
                self.high_scores.append(self.score)
                self.high_scores.sort(reverse=True)
                if len(self.high_scores) > 5:
                    self.high_scores.pop()

        elif result == "coin":
            self.collected_coins += 1
            pts = int(50 * self.score_multiplier)
            self.score += pts
            self.floaters.append({'text': f'+{pts}', 'color': (255, 225, 50),
                              'x': int(self.player.get_screen_x()),
                              'y': int(self.player.base_y - self.player.y_offset - 30),
                              'timer': 0.85})

        elif result == "boost":
            self.boost_active     = True
            self.boost_timer      = self.settings.BOOST_DURATION
            self.score_multiplier = self.settings.BOOST_MULTIPLIER
            self.floaters.append({'text': f'x{self.settings.BOOST_MULTIPLIER}  BOOST !', 'color': (200, 80, 255),
                              'x': self.width // 2, 'y': int(self.height * 0.44), 'timer': 1.2})

        self.score += int(10 * self.score_multiplier)

        self.game_time += dt
        if not self.boss.active and not self.boss.defeated and self.game_time >= self.settings.BOSS_TRIGGER_TIME:
            self.boss.activate()
            self.floaters.append({'text': '! 404 AWAKENS !', 'color': (255, 50, 255),
                              'x': self.width // 2, 'y': int(self.height * 0.38), 'timer': 2.8})

        boss_result = self.boss.update(dt, self.player.getLane(), self.invincible_timer > 0, self.player.getIsJumping())

        if boss_result == 'player_hit' and self.lives > 0:
            self.lives -= 1
            self.invincible_timer = self.settings.INVINCIBLE_DURATION
            self.hit_flash_timer = self.settings.INVINCIBLE_DURATION * 0.55
            self.player.trigger_hit()
            if self.lives <= 0:
                self.game_state = "game_over"
                self.high_scores.append(self.score)
                self.high_scores.sort(reverse=True)
                if len(self.high_scores) > 5:
                    self.high_scores.pop()

        elif boss_result == 'boss_defeated':
            bonus = 2000
            self.score += bonus
            self.floaters.append({'text': f'404 DEFEATED!  +{bonus}', 'color': (255, 220, 50),
                              'x': self.width // 2, 'y': int(self.height * 0.32), 'timer': 3.2})
