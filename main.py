import os
import sys
import pygame
import math
import random

from screeninfo import get_monitors
from Classes.Background import Background
from Classes.Player import Player
from Classes.EntityManager import EntityManager
from Classes.Boss import Boss
from Classes.HeadController import HeadController
from Classes.Settings import Settings
import Classes.UI as ui
from Classes.Screens import ScreenRenderer

x = 0
y = 30
os.environ['SDL_VIDEO_WINDOW_POS'] = f'{x},{y}'
import pgzrun

WIDTH  = get_monitors()[0].width
HEIGHT = get_monitors()[0].height - y
TITLE  = "404GameNotFound"

# ── Game objects ───────────────────────────────────────────────────────────────
settings      = Settings()
road          = Background(HEIGHT, WIDTH)
player        = Player(HEIGHT, WIDTH)
entityManager = EntityManager(HEIGHT, WIDTH)
boss          = Boss(HEIGHT, WIDTH)
head_ctrl     = HeadController()

ui.init(WIDTH, HEIGHT, settings.PIXEL_FONT)
renderer = ScreenRenderer(WIDTH, HEIGHT, settings)

# ── Game state ─────────────────────────────────────────────────────────────────
# "menu" | "tutorial" | "settings" | "playing" | "game_over"
game_state        = "menu"
MOVE_OFFSET       = 0.0
SPEED             = settings.BASE_SPEED
score             = 0
lives             = settings.MAX_LIVES
invincible_timer  = 0.0
boost_active      = False
boost_timer       = 0.0
score_multiplier  = 1
collected_coins   = 0
coin_boost_active = False
coin_boost_timer  = 0.0
game_time         = 0.0

# ── Floaters (score / event pop-ups) ──────────────────────────────────────────
_floaters = []

# ── Hit flash ─────────────────────────────────────────────────────────────────
_hit_flash_timer = 0.0

# ── Button click-flash registry (rect_tuple -> seconds_remaining) ──────────────
_click_flash_rects: dict = {}

# ── Head cursor (menu navigation when head control is active) ─────────────────
_hcursor_pos = None

# ── Tutorial / Settings scroll ────────────────────────────────────────────────
_tutorial_scroll     = 0.0
_tutorial_max_scroll = 0
_settings_scroll     = 0.0
_settings_max_scroll = 0


# ── Helpers ────────────────────────────────────────────────────────────────────

def _flash_btn(r):
    """Register a short click-flash for rect r."""
    _click_flash_rects[(r.x, r.y, r.w, r.h)] = 0.18


def _tick_floaters(dt):
    for f in _floaters:
        f['y']    -= 60 * dt
        f['timer'] -= dt
    _floaters[:] = [f for f in _floaters if f['timer'] > 0]


# ── Input ──────────────────────────────────────────────────────────────────────

def on_key_down(key):
    global game_state, coin_boost_active, coin_boost_timer, collected_coins

    if key == keys.ESCAPE:
        if game_state in ("tutorial", "settings", "playing", "game_over"):
            game_state = "menu"
        elif game_state == "menu":
            sys.exit(0)
        return

    if key == keys.SPACE:
        if   game_state == "menu":
            _start_game()
        elif game_state in ("tutorial", "settings"):
            game_state = "menu"
        elif game_state == "playing":
            player.jump()
        elif game_state == "game_over":
            reset()
        return

    if game_state != "playing":
        return

    if   key in (keys.LEFT,  keys.A):
        player.move_left()
    elif key in (keys.RIGHT, keys.D):
        player.move_right()
    elif key in (keys.UP, keys.W):
        if collected_coins >= settings.COIN_BOOST_COST and not coin_boost_active:
            collected_coins  -= settings.COIN_BOOST_COST
            coin_boost_active = True
            coin_boost_timer  = settings.COIN_BOOST_DURATION
            _floaters.append({'text': 'SPEED  x2 !', 'color': (80, 210, 255),
                               'x': WIDTH // 2, 'y': int(HEIGHT * 0.44), 'timer': 1.4})
    elif key in (keys.DOWN, keys.S):
        if boss.active and not boss.defeated and collected_coins > 0:
            collected_coins -= 1
            boss.fire_player_shot(player.getLane(), 2.0 if coin_boost_active else 1.0)


def on_mouse_wheel(dy):
    global _tutorial_scroll, _settings_scroll
    step = 120
    if game_state == "tutorial":
        _tutorial_scroll = max(0.0, min(float(_tutorial_max_scroll), _tutorial_scroll - dy * step))
    elif game_state == "settings":
        _settings_scroll = max(0.0, min(float(_settings_max_scroll), _settings_scroll - dy * step))


def on_mouse_down(pos):
    global game_state, _tutorial_scroll, _settings_scroll
    if game_state == "menu":
        if   ui.btn_rect('play').collidepoint(pos):
            _flash_btn(ui.btn_rect('play'));     _start_game()
        elif ui.btn_rect('tutorial').collidepoint(pos):
            _flash_btn(ui.btn_rect('tutorial')); game_state = "tutorial"; _tutorial_scroll = 0.0
        elif ui.btn_rect('settings').collidepoint(pos):
            _flash_btn(ui.btn_rect('settings')); game_state = "settings"; _settings_scroll = 0.0
        elif ui.btn_rect('exit').collidepoint(pos):
            _flash_btn(ui.btn_rect('exit'));     sys.exit(0)
    elif game_state == "tutorial":
        _tbw = int(WIDTH * 0.22);  _tbh = int(HEIGHT * 0.088)
        _panel_b = HEIGHT - int(HEIGHT * 0.02)
        _back_y  = _panel_b - int(HEIGHT * 0.10) - int(HEIGHT * 0.015) // 2
        tbr = pygame.Rect(WIDTH // 2 - _tbw // 2, _back_y, _tbw, _tbh)
        if tbr.collidepoint(pos):
            _flash_btn(tbr);  game_state = "menu"
    elif game_state == "settings":
        if   ui.btn_rect('back').collidepoint(pos):
            _flash_btn(ui.btn_rect('back'));       game_state = "menu"
        elif ui.btn_rect('colorblind').collidepoint(pos):
            _flash_btn(ui.btn_rect('colorblind')); settings.cycle_colorblind()
        elif ui.btn_rect('headctrl').collidepoint(pos) and head_ctrl.available:
            _flash_btn(ui.btn_rect('headctrl'));   head_ctrl.toggle()
    elif game_state == "game_over":
        if   ui.btn_rect('go_play').collidepoint(pos):
            _flash_btn(ui.btn_rect('go_play'));     reset()
        elif ui.btn_rect('go_menu').collidepoint(pos):
            _flash_btn(ui.btn_rect('go_menu'));     game_state = "menu"
        elif ui.btn_rect('go_settings').collidepoint(pos):
            _flash_btn(ui.btn_rect('go_settings')); game_state = "settings"
        elif ui.btn_rect('go_exit').collidepoint(pos):
            _flash_btn(ui.btn_rect('go_exit'));     sys.exit(0)


# ── Core game loop ─────────────────────────────────────────────────────────────

def _start_game():
    reset()


def update(dt):
    global MOVE_OFFSET, SPEED, game_state, score, lives
    global invincible_timer, boost_active, boost_timer, score_multiplier
    global collected_coins, coin_boost_active, coin_boost_timer
    global _hit_flash_timer, game_time
    global _tutorial_scroll, _settings_scroll
    global _hcursor_pos, _tutorial_max_scroll, _settings_max_scroll

    # Tick button click-flash timers
    for _k in list(_click_flash_rects):
        _click_flash_rects[_k] -= dt
        if _click_flash_rects[_k] <= 0:
            del _click_flash_rects[_k]

    # Road always animates so menus have a live background
    SPEED        = settings.BASE_SPEED * (2.0 if coin_boost_active else 1.0)
    MOVE_OFFSET += SPEED * dt * 60
    if MOVE_OFFSET >= 1.0:
        MOVE_OFFSET -= 1.0
    road.update(MOVE_OFFSET, dt, SPEED)

    _tick_floaters(dt)

    # Scrollable menus — UP/DOWN or W/S to scroll
    if game_state == "tutorial":
        spd = HEIGHT * 0.7
        if keyboard.up or keyboard.w:
            _tutorial_scroll = max(0.0, _tutorial_scroll - spd * dt)
        if keyboard.down or keyboard.s:
            _tutorial_scroll = min(float(_tutorial_max_scroll), _tutorial_scroll + spd * dt)
    elif game_state == "settings":
        spd = HEIGHT * 0.7
        if keyboard.up or keyboard.w:
            _settings_scroll = max(0.0, _settings_scroll - spd * dt)
        if keyboard.down or keyboard.s:
            _settings_scroll = min(float(_settings_max_scroll), _settings_scroll + spd * dt)

    # ── Head cursor (menu navigation) ────────────────────────────────────────
    if head_ctrl.enabled and game_state != "playing":
        pos = head_ctrl.get_head_norm_pos()
        if pos:
            _hcursor_pos = (
                max(0, min(WIDTH  - 1, int(pos[0] * WIDTH))),
                max(0, min(HEIGHT - 1, int(pos[1] * HEIGHT))),
            )
        if head_ctrl.consume_shoot():
            if _hcursor_pos:
                on_mouse_down(_hcursor_pos)
    elif game_state == "playing":
        _hcursor_pos = None

    if game_state != "playing":
        return

    player.update(dt)

    if invincible_timer > 0:
        invincible_timer -= dt
    if _hit_flash_timer > 0:
        _hit_flash_timer -= dt
    if boost_active:
        boost_timer -= dt
        if boost_timer <= 0:
            boost_active = False;  boost_timer = 0.0;  score_multiplier = 1
    if coin_boost_active:
        coin_boost_timer -= dt
        if coin_boost_timer <= 0:
            coin_boost_active = False;  coin_boost_timer = 0.0

    # ── Head controller input ─────────────────────────────────────────────────
    if head_ctrl.enabled:
        target = head_ctrl.consume_target_lane()
        if target is not None:
            player.current_lane = target
        while head_ctrl.consume_jump():
            player.jump()
        if head_ctrl.consume_shoot() and boss.active and not boss.defeated and collected_coins > 0:
            collected_coins -= 1
            boss.fire_player_shot(player.getLane(),
                                  2.0 if coin_boost_active else 1.0)

    result = entityManager.update(
        dt, player.getLane(), player.getIsJumping(), SPEED, invincible_timer > 0)

    if result == "dead":
        lives           -= 1
        invincible_timer = settings.INVINCIBLE_DURATION
        _hit_flash_timer = settings.INVINCIBLE_DURATION * 0.55
        player.trigger_hit()
        if lives <= 0:
            game_state = "game_over"
            settings.add_score(score)

    elif result == "coin":
        collected_coins += 1
        pts = int(50 * score_multiplier)
        score += pts
        _floaters.append({'text': f'+{pts}', 'color': (255, 225, 50),
                          'x': int(player.get_screen_x()),
                          'y': int(player.base_y - player.y_offset - 30),
                          'timer': 0.85})

    elif result == "boost":
        boost_active     = True
        boost_timer      = settings.BOOST_DURATION
        score_multiplier = settings.BOOST_MULTIPLIER
        _floaters.append({'text': f'x{settings.BOOST_MULTIPLIER}  BOOST !', 'color': (200, 80, 255),
                          'x': WIDTH // 2, 'y': int(HEIGHT * 0.44), 'timer': 1.2})

    score += int(10 * score_multiplier)

    # ── Boss ──────────────────────────────────────────────────────────────────
    game_time += dt
    if not boss.active and not boss.defeated and game_time >= settings.BOSS_TRIGGER_TIME:
        boss.activate()
        _floaters.append({'text': '! 404 AWAKENS !', 'color': (255, 50, 255),
                          'x': WIDTH // 2, 'y': int(HEIGHT * 0.38), 'timer': 2.8})

    boss_result = boss.update(dt, player.getLane(), invincible_timer > 0, player.getIsJumping())

    if boss_result == 'player_hit' and lives > 0:
        lives           -= 1
        invincible_timer = settings.INVINCIBLE_DURATION
        _hit_flash_timer = settings.INVINCIBLE_DURATION * 0.55
        player.trigger_hit()
        if lives <= 0:
            game_state = "game_over"
            settings.add_score(score)

    elif boss_result == 'boss_defeated':
        bonus = 2000
        score += bonus
        _floaters.append({'text': f'404 DEFEATED!  +{bonus}', 'color': (255, 220, 50),
                          'x': WIDTH // 2, 'y': int(HEIGHT * 0.32), 'timer': 3.2})


def reset():
    global MOVE_OFFSET, score, game_state, lives, collected_coins
    global invincible_timer, boost_active, boost_timer, score_multiplier
    global coin_boost_active, coin_boost_timer, _hit_flash_timer, game_time
    MOVE_OFFSET      = 0.0
    score            = 0
    game_state       = "playing"
    lives            = settings.MAX_LIVES
    collected_coins  = 0
    invincible_timer = 0.0
    game_time        = 0.0
    boost_active     = False;  boost_timer     = 0.0;  score_multiplier = 1
    coin_boost_active= False;  coin_boost_timer = 0.0
    _hit_flash_timer = 0.0
    _floaters.clear()
    entityManager.reset()
    player.reset()
    boss.reset()


# ── Draw ───────────────────────────────────────────────────────────────────────

def draw():
    global _tutorial_max_scroll, _settings_max_scroll

    ui.begin_frame(_hcursor_pos, _click_flash_rects, settings.colorblind_mode)
    ui.load_heart_imgs()
    screen.clear()
    road.draw(screen)

    if game_state == "playing":
        boss.draw(screen, ui.px_text, ui.font, settings.colorblind_mode)
        entityManager.draw_bg(screen, 345)
        player.draw(screen)
        entityManager.draw_fg(screen, 345)
        screen.surface.blit(ui.get_vignette(), (0, 0))
        renderer.draw_floaters(screen.surface, _floaters)
        renderer.draw_hit_flash(screen.surface, _hit_flash_timer)
        renderer.draw_hud(screen.surface, lives, score, score_multiplier,
                          boost_active, boost_timer, coin_boost_active, coin_boost_timer,
                          collected_coins, invincible_timer, boss)
        renderer.draw_head_preview(screen.surface, head_ctrl)

    elif game_state == "game_over":
        boss.draw(screen, ui.px_text, ui.font, settings.colorblind_mode)
        entityManager.draw_bg(screen, 345)
        player.draw(screen)
        entityManager.draw_fg(screen, 345)
        screen.surface.blit(ui.get_vignette(), (0, 0))
        renderer.draw_game_over(screen.surface, score, collected_coins, settings.high_scores)

    elif game_state == "menu":
        screen.surface.blit(ui.get_vignette(), (0, 0))
        renderer.draw_menu(screen.surface, settings.high_scores)

    elif game_state == "tutorial":
        screen.surface.blit(ui.get_vignette(), (0, 0))
        _tutorial_max_scroll = renderer.draw_tutorial(screen.surface, _tutorial_scroll)

    elif game_state == "settings":
        screen.surface.blit(ui.get_vignette(), (0, 0))
        _settings_max_scroll = renderer.draw_settings(screen.surface, _settings_scroll, head_ctrl)

    if game_state != "playing":
        ui.draw_head_cursor(screen.surface, _hcursor_pos)
    ui.apply_colorblind_filter(screen.surface)


pgzrun.go()
