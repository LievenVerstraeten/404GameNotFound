import os
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

x = 0
y = 30
os.environ['SDL_VIDEO_WINDOW_POS'] = f'{x},{y}'
import pgzrun

WIDTH  = get_monitors()[0].width
HEIGHT = get_monitors()[0].height - y
TITLE  = "404GameNotFound"

# ── Settings & game objects ────────────────────────────────────────────────────
settings      = Settings()
road          = Background(HEIGHT, WIDTH)
player        = Player(HEIGHT, WIDTH)
entityManager = EntityManager(HEIGHT, WIDTH)
boss          = Boss(HEIGHT, WIDTH)
head_ctrl     = HeadController()

# ── Game state ─────────────────────────────────────────────────────────────────
# "menu" | "tutorial" | "settings" | "playing" | "game_over"
game_state        = "menu"
MOVE_OFFSET       = 0.0
SPEED             = settings.BASE_SPEED
score             = 0
high_scores       = []
lives             = settings.MAX_LIVES
invincible_timer  = 0.0
boost_active      = False
boost_timer       = 0.0
score_multiplier  = 1
collected_coins   = 0
coin_boost_active = False
coin_boost_timer  = 0.0
game_time         = 0.0    # total seconds played this run

# ── Floaters (score / event pop-ups) ──────────────────────────────────────────
_floaters = []   # [{text, color, x, y, timer}]

# ── Hit flash ─────────────────────────────────────────────────────────────────
_hit_flash_timer = 0.0

# ── UI caches (lazily built after pygame init) ────────────────────────────────
_heart_img      = None
_dark_heart_img = None
_fonts          = {}
_vignette_surf  = None


# ── Pixel font helpers ─────────────────────────────────────────────────────────
_PIXEL_FONT = settings.PIXEL_FONT


def _font(size):
    """Return a cached font."""
    if size not in _fonts:
        pygame.font.init()
        if _PIXEL_FONT:
            try:
                f = pygame.font.Font(_PIXEL_FONT, size)
                f.render("A", True, (255, 255, 255))   # raises if bad file
                _fonts[size] = f
            except Exception:
                pass
        if size not in _fonts:
            _fonts[size] = pygame.font.SysFont(None, size)
    return _fonts[size]


def _px_text(surf, text, pos, size, color,
             shadow_col=None, center=False, outline=None):
    """Pixel-perfect text with Minecraft-style black outline.
    outline=None auto-sizes to 1 or 2px based on font size.
    Returns (text_w, text_h)."""
    f        = _font(size)
    rendered = f.render(str(text), True, color)
    rx, ry   = pos
    if center:
        rx -= rendered.get_width()  // 2
        ry -= rendered.get_height() // 2

    # Minecraft-style outline: draw black glyph in 8 directions, then main color
    ow = (max(1, size // 40) if outline is None else outline)
    dark = f.render(str(text), True, (0, 0, 0))
    for dx in range(-ow, ow + 1):
        for dy in range(-ow, ow + 1):
            if dx == 0 and dy == 0:
                continue
            surf.blit(dark, (rx + dx, ry + dy))

    surf.blit(rendered, (rx, ry))
    return rendered.get_width(), rendered.get_height()


# ── Pixel-art UI panels & buttons ─────────────────────────────────────────────
def _draw_panel(surf, rect,
                bg=(12, 12, 30, 215), border=(255, 220, 50), bw=3):
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    panel.fill(bg)
    surf.blit(panel, rect.topleft)
    pygame.draw.rect(surf, border, rect, bw)


def _draw_button(surf, rect, label, size=24, hover=False):
    bg   = (55, 42, 8,  240) if hover else (25, 20, 5,  220)
    bord = (255, 235, 90)    if hover else (185, 152, 28)
    tcol = (255, 248, 140)   if hover else (215, 190, 75)
    _draw_panel(surf, rect, bg=bg, border=bord, bw=3)
    _px_text(surf, label, (rect.centerx, rect.centery), size, tcol, center=True)


def _draw_coin_icon(surf, cx, cy, r=9):
    """Draw a tiny pixel-art coin centred at (cx, cy) with radius r."""
    pygame.draw.rect(surf, (200, 140,  0), (cx - r,     cy - r,     r * 2,     r * 2))
    pygame.draw.rect(surf, (255, 210, 40), (cx - r + 2, cy - r + 2, r * 2 - 4, r * 2 - 4))
    pygame.draw.rect(surf, (255, 240,100), (cx - r + 4, cy - r + 4, r * 2 - 8, r * 2 - 8))
    pygame.draw.rect(surf, (140,  95,  0), (cx - r,     cy - r,     r * 2,     r * 2), 2)


# ── Button layout (all positions in one place) ────────────────────────────────
def _btn(name):
    cx  = WIDTH  // 2
    bw  = int(WIDTH  * 0.17)
    bh  = int(HEIGHT * 0.073)
    gap = int(bh * 0.38)
    my  = HEIGHT // 2 - bh // 2
    pos = {
        'play':     (cx - bw // 2, my),
        'tutorial': (cx - bw // 2, my +  bh + gap),
        'settings': (cx - bw // 2, my + (bh + gap) * 2),
        'back':        (cx - bw // 2, int(HEIGHT * 0.84)),
        'headctrl':    (cx - bw // 2, int(HEIGHT * 0.63)),
        'colorblind':  (cx - bw // 2, int(HEIGHT * 0.73)),
    }
    bx, by = pos.get(name, (0, 0))
    return pygame.Rect(bx, by, bw, bh)


# ── Vignette (computed once, then cached) ─────────────────────────────────────
def _get_vignette():
    global _vignette_surf
    if _vignette_surf is None:
        _vignette_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        steps = 22
        eh    = int(HEIGHT * 0.15)
        ew    = int(WIDTH  * 0.10)
        for i in range(steps):
            t  = i / steps
            h  = max(1, eh // steps + 1)
            wa = max(1, ew // steps + 1)
            a_h = int(95  * (1 - t) ** 2)
            a_w = int(65  * (1 - t) ** 2)
            yt  = int(t * eh)
            yb  = HEIGHT - 1 - int(t * eh)
            xl  = int(t * ew)
            xr  = WIDTH  - 1 - int(t * ew)
            pygame.draw.rect(_vignette_surf, (0, 0, 0, a_h), (0,  yt, WIDTH,  h))
            pygame.draw.rect(_vignette_surf, (0, 0, 0, a_h), (0,  yb, WIDTH,  h))
            pygame.draw.rect(_vignette_surf, (0, 0, 0, a_w), (xl,  0, wa, HEIGHT))
            pygame.draw.rect(_vignette_surf, (0, 0, 0, a_w), (xr,  0, wa, HEIGHT))
    return _vignette_surf


# ── Heart images ──────────────────────────────────────────────────────────────
def _load_heart_imgs():
    global _heart_img, _dark_heart_img
    if _heart_img is not None:
        return
    hs = int(HEIGHT * 0.135)   # 3× original 0.045
    try:
        raw = pygame.image.load("images/full_heart.webp").convert_alpha()
    except Exception:
        raw = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.polygon(raw, (220, 30, 30),
                            [(4,10),(10,4),(16,8),(22,4),(28,10),
                             (28,18),(16,30),(4,18)])
    _heart_img      = pygame.transform.scale(raw, (hs, hs))
    _dark_heart_img = _heart_img.copy()
    _dark_heart_img.fill((15, 15, 15, 200), special_flags=pygame.BLEND_RGBA_MULT)


# ── Input ──────────────────────────────────────────────────────────────────────
def on_key_down(key):
    global game_state, coin_boost_active, coin_boost_timer, collected_coins

    if key == keys.ESCAPE:
        if game_state in ("tutorial", "settings"):
            game_state = "menu"
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
            speed_mult = 2.0 if coin_boost_active else 1.0
            boss.fire_player_shot(player.getLane(), speed_mult)


def on_mouse_down(pos):
    global game_state
    if game_state == "menu":
        if   _btn('play').collidepoint(pos):     _start_game()
        elif _btn('tutorial').collidepoint(pos): game_state = "tutorial"
        elif _btn('settings').collidepoint(pos): game_state = "settings"
    elif game_state == "tutorial":
        if _btn('back').collidepoint(pos):       game_state = "menu"
    elif game_state == "settings":
        if   _btn('back').collidepoint(pos):       game_state = "menu"
        elif _btn('colorblind').collidepoint(pos): settings.colorblind_mode = (settings.colorblind_mode + 1) % 3
        elif _btn('headctrl').collidepoint(pos) and head_ctrl.available:
            head_ctrl.toggle()
    elif game_state == "game_over":
        if _btn('back').collidepoint(pos):       reset()


# ── Core game loop ────────────────────────────────────────────────────────────
def _start_game():
    reset()                    # reset() sets game_state = "playing"


def update(dt):
    global MOVE_OFFSET, SPEED, game_state, score, lives
    global invincible_timer, boost_active, boost_timer, score_multiplier
    global collected_coins, coin_boost_active, coin_boost_timer
    global _hit_flash_timer, game_time

    # Road always animates so menus have a live background
    SPEED        = settings.BASE_SPEED * (2.0 if coin_boost_active else 1.0)
    MOVE_OFFSET += SPEED * dt * 60   # dt-corrected so speed stays constant at any FPS
    if MOVE_OFFSET >= 1.0:
        MOVE_OFFSET -= 1.0
    road.update(MOVE_OFFSET, dt, SPEED)

    _tick_floaters(dt)

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
        d = head_ctrl.consume_lane_change()
        if   d == -1: player.move_left()
        elif d ==  1: player.move_right()
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
            high_scores.append(score)
            high_scores.sort(reverse=True)
            if len(high_scores) > 5:
                high_scores.pop()

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
            high_scores.append(score)
            high_scores.sort(reverse=True)
            if len(high_scores) > 5:
                high_scores.pop()

    elif boss_result == 'boss_defeated':
        bonus = 2000
        score += bonus
        _floaters.append({'text': f'404 DEFEATED!  +{bonus}', 'color': (255, 220, 50),
                          'x': WIDTH // 2, 'y': int(HEIGHT * 0.32), 'timer': 3.2})


def _tick_floaters(dt):
    for f in _floaters:
        f['y']    -= 60 * dt
        f['timer'] -= dt
    _floaters[:] = [f for f in _floaters if f['timer'] > 0]


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


# ── Draw dispatcher ────────────────────────────────────────────────────────────
def draw():
    _load_heart_imgs()
    screen.clear()
    road.draw(screen)

    if game_state == "playing":
        boss.draw(screen, _px_text, _font, settings.colorblind_mode)
        entityManager.draw_bg(screen, 345)
        player.draw(screen)
        entityManager.draw_fg(screen, 345)
        screen.surface.blit(_get_vignette(), (0, 0))
        _draw_floaters()
        _draw_hit_flash()
        _draw_hud()
        _draw_head_preview()

    elif game_state == "game_over":
        boss.draw(screen, _px_text, _font, settings.colorblind_mode)
        entityManager.draw_bg(screen, 345)
        player.draw(screen)
        entityManager.draw_fg(screen, 345)
        screen.surface.blit(_get_vignette(), (0, 0))
        _draw_game_over()

    elif game_state == "menu":
        screen.surface.blit(_get_vignette(), (0, 0))
        _draw_menu()

    elif game_state == "tutorial":
        screen.surface.blit(_get_vignette(), (0, 0))
        _draw_tutorial()

    elif game_state == "settings":
        screen.surface.blit(_get_vignette(), (0, 0))
        _draw_settings()


# ── HUD ────────────────────────────────────────────────────────────────────────
def _draw_hud():
    surf = screen.surface
    pad  = int(HEIGHT * 0.018)
    hs   = _heart_img.get_width() if _heart_img else int(HEIGHT * 0.135)
    gap  = int(hs * 0.25)

    # Score — 3× font size
    _px_text(surf, f"SCORE  {score:07d}", (pad, pad), 102, (255, 240, 80))

    # Coin counter + progress bar — all 3× larger
    coin_y = pad + 114
    coin_r = int(HEIGHT * 0.039)
    _draw_coin_icon(surf, pad + coin_r, coin_y + coin_r, coin_r)
    _px_text(surf, f" {collected_coins:02d}/{settings.COIN_BOOST_COST}   UP = BOOST",
             (pad + coin_r * 2 + 4, coin_y), 60, (255, 210, 55))

    bar_w  = int(WIDTH * 0.27)
    bar_h  = 15
    bar_y  = coin_y + 72
    fill   = int(bar_w * min(1.0, collected_coins / settings.COIN_BOOST_COST))
    pygame.draw.rect(surf, (55, 44, 8),   (pad, bar_y, bar_w, bar_h))
    pygame.draw.rect(surf, (255, 210, 40),(pad, bar_y, fill,  bar_h))
    pygame.draw.rect(surf, (160, 130, 18),(pad, bar_y, bar_w, bar_h), 2)

    # Active boost labels — colors vary by accessibility mode
    boost_label_y = bar_y + bar_h + 21
    if   settings.colorblind_mode == 1: key_col, speed_col = (255, 165, 0),   ( 30, 100, 255)  # orange / blue
    elif settings.colorblind_mode == 2: key_col, speed_col = (240, 240, 240), (160, 160, 160)  # white / gray
    else:                      key_col, speed_col = (200,  80, 255), ( 80, 210, 255)  # purple / cyan
    if boost_active:
        secs = int(boost_timer) + 1
        _px_text(surf, f"KEY x{score_multiplier}  {secs}s",
                 (pad, boost_label_y), 72, key_col)
        boost_label_y += 84
    if coin_boost_active:
        secs = int(coin_boost_timer) + 1
        _px_text(surf, f"SPEED x2  {secs}s",
                 (pad, boost_label_y), 72, speed_col)

    # Hearts (top-right)
    if _heart_img:
        total_w = settings.MAX_LIVES * hs + (settings.MAX_LIVES - 1) * gap
        sx      = WIDTH - total_w - pad
        for i in range(settings.MAX_LIVES):
            img = _heart_img if i < lives else _dark_heart_img
            surf.blit(img, (sx + i * (hs + gap), pad))
        # Accessibility modes add a numeric label so count is never color-only
        if settings.colorblind_mode > 0:
            _px_text(surf, f"LIVES  {lives}/{settings.MAX_LIVES}",
                     (WIDTH - total_w // 2 - pad, pad + hs + 6),
                     28, (255, 255, 255), center=True)


def _draw_floaters():
    for f in _floaters:
        _px_text(screen.surface, f['text'],
                 (int(f['x']), int(f['y'])), 28, f['color'], center=True)


def _draw_hit_flash():
    if _hit_flash_timer > 0:
        a     = int(110 * min(1.0, _hit_flash_timer / (settings.INVINCIBLE_DURATION * 0.55)))
        flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        # Accessibility flash colours
        if   settings.colorblind_mode == 1: flash.fill((0,   80, 210, a))   # blue
        elif settings.colorblind_mode == 2: flash.fill((220, 220, 220, a))  # white
        else:                      flash.fill((210,   0,   0, a))  # red
        screen.surface.blit(flash, (0, 0))


def _draw_head_preview():
    """Blit the live annotated webcam frame to the bottom-right corner."""
    if not head_ctrl.enabled:
        return
    frame = head_ctrl.get_preview_frame()   # numpy uint8 RGB, or None
    if frame is None:
        # Show an error/waiting badge instead
        surf  = screen.surface
        pw    = int(WIDTH  * 0.18)
        ph    = int(HEIGHT * 0.07)
        px    = WIDTH  - pw - int(WIDTH * 0.012)
        py    = HEIGHT - ph - int(HEIGHT * 0.012)
        badge = pygame.Surface((pw, ph), pygame.SRCALPHA)
        badge.fill((20, 0, 0, 200))
        surf.blit(badge, (px, py))
        msg = head_ctrl.error_msg or "Opening camera…"
        _px_text(surf, msg[:38], (px + pw // 2, py + ph // 2),
                 12, (255, 80, 80), center=True)
        pygame.draw.rect(surf, (180, 0, 0), (px, py, pw, ph), 2)
        return

    # Convert numpy RGB → pygame Surface (axes must be W×H×3)
    try:
        cam_surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
    except Exception:
        return

    pw = int(WIDTH  * 0.20)
    ph = int(pw * frame.shape[0] / frame.shape[1])   # keep aspect
    cam_scaled = pygame.transform.scale(cam_surf, (pw, ph))

    margin = int(WIDTH * 0.012)
    px = WIDTH  - pw - margin
    py = HEIGHT - ph - margin

    screen.surface.blit(cam_scaled, (px, py))
    # Coloured border: green = face found, red = no face
    border_col = (0, 220, 80) if head_ctrl.enabled else (200, 50, 50)
    pygame.draw.rect(screen.surface, border_col, (px, py, pw, ph), 3)


# ── Menu ───────────────────────────────────────────────────────────────────────
def _draw_menu():
    surf = screen.surface
    cx   = WIDTH // 2

    # Title card
    tp = pygame.Rect(cx - int(WIDTH * 0.27), int(HEIGHT * 0.10),
                     int(WIDTH * 0.54), int(HEIGHT * 0.24))
    _draw_panel(surf, tp, bg=(8, 8, 22, 215), border=(255, 220, 50), bw=4)
    _px_text(surf, "404",            (cx, int(HEIGHT * 0.165)), 78, (255, 70, 70),
             shadow_col=(80, 0, 0), center=True)
    _px_text(surf, "GAME NOT FOUND", (cx, int(HEIGHT * 0.255)), 30, (255, 220, 50),
             center=True)

    if high_scores:
        _px_text(surf, f"BEST  {high_scores[0]:07d}", (cx, int(HEIGHT * 0.325)),
                 22, (170, 215, 170), center=True)

    _draw_button(surf, _btn('play'),     "  PLAY  ",  30)
    _draw_button(surf, _btn('tutorial'), "TUTORIAL",  24)
    _draw_button(surf, _btn('settings'), "SETTINGS",  24)

    _px_text(surf, "SPACE  or  click  PLAY  to  start",
             (cx, int(HEIGHT * 0.91)), 18, (140, 140, 140), center=True)


# ── Tutorial ───────────────────────────────────────────────────────────────────
def _draw_tutorial():
    surf = screen.surface
    cx   = WIDTH // 2

    panel = pygame.Rect(cx - int(WIDTH * 0.30), int(HEIGHT * 0.06),
                        int(WIDTH * 0.60), int(HEIGHT * 0.80))
    _draw_panel(surf, panel, bg=(8, 8, 22, 222), bw=4)

    ty = int(HEIGHT * 0.10)
    _px_text(surf, "HOW  TO  PLAY", (cx, ty), 36, (255, 220, 50), center=True)
    ty += int(HEIGHT * 0.08)

    lx = cx - int(WIDTH * 0.26)
    dx = cx - int(WIDTH * 0.08)
    rows = [
        ("MOVE",       "<  >  Arrow Keys   Change lane"),
        ("JUMP",       "SPACE   Jump   (double jump OK)"),
        ("BOOST",      "UP Arrow   Speed x2   costs 10 coins"),
        ("", ""),
        ("COINS",      "Gold coins   ->   +score  +coin count"),
        ("ROCK",       "Small rock   ->   jump over it"),
        ("BOULDER",    "Big boulder  ->   DOUBLE JUMP"),
        ("KEY",        "Boost key    ->   score x3  for 6s"),
        ("", ""),
        ("LIVES",      "3 hearts   one lost per crash"),
        ("INVULN",     "Brief red flash after each hit"),
        ("DAY/NIGHT",  "World cycles every 60 seconds"),
        ("", ""),
        ("BOSS",       "404 boss appears after 60 seconds"),
        ("DODGE",      "1 and 0 projectiles — change lane!"),
        ("SHOOT",      "DOWN / S — fire coin at boss"),
        ("BOSS HP",    "2 coin hits = 1 boss heart  (10 total)"),
        ("BOOST SHOT", "Speed boost doubles coin shot speed"),
    ]
    for label, desc in rows:
        if not label:
            ty += int(HEIGHT * 0.022);  continue
        _px_text(surf, label, (lx, ty), 21, (90, 210, 255))
        _px_text(surf, desc,  (dx, ty), 21, (215, 215, 215))
        ty += int(HEIGHT * 0.050)

    _draw_button(surf, _btn('back'), "BACK", 24)
    _px_text(surf, "ESC or SPACE to go back",
             (cx, int(HEIGHT * 0.93)), 17, (120, 120, 120), center=True)


# ── Settings ───────────────────────────────────────────────────────────────────
def _draw_settings():
    surf = screen.surface
    cx   = WIDTH // 2

    panel = pygame.Rect(cx - int(WIDTH * 0.26), int(HEIGHT * 0.10),
                        int(WIDTH * 0.52), int(HEIGHT * 0.65))
    _draw_panel(surf, panel, bg=(8, 8, 22, 222), bw=4)

    ty = int(HEIGHT * 0.145)
    _px_text(surf, "SETTINGS", (cx, ty), 36, (255, 220, 50), center=True)
    ty += int(HEIGHT * 0.09)

    lx = cx - int(WIDTH * 0.22)
    vx = cx + int(WIDTH * 0.01)
    rows = [
        ("Move lane",    "Left / Right Arrow"),
        ("Jump",         "SPACE   (double jump)"),
        ("Coin boost",   f"UP Arrow  —  costs {settings.COIN_BOOST_COST} coins"),
        ("", ""),
        ("Boost dur.",   f"{settings.COIN_BOOST_DURATION:.0f}s  speed x2"),
        ("Key boost",    f"x{settings.BOOST_MULTIPLIER} score  for  {settings.BOOST_DURATION:.0f}s"),
        ("Day cycle",    "60s  per  day / night"),
        ("", ""),
        ("Restart",      "SPACE on Game Over screen"),
    ]
    for label, val in rows:
        if not label:
            ty += int(HEIGHT * 0.022);  continue
        _px_text(surf, label + ":", (lx, ty), 21, (130, 200, 255))
        _px_text(surf, val,         (vx, ty), 21, (215, 210, 175))
        ty += int(HEIGHT * 0.053)

    # Head control toggle
    if head_ctrl.available:
        hc_label = "HEAD CONTROL:  ON " if head_ctrl.enabled else "HEAD CONTROL:  OFF"
        hc_desc  = ("Nod L/R = lane    Nod down = jump    Open mouth = shoot"
                    if head_ctrl.enabled else
                    "Click to enable webcam head tracking")
        hc_col   = (80, 255, 160) if head_ctrl.enabled else (180, 180, 180)
    else:
        hc_label = "HEAD CONTROL:  N/A"
        hc_desc  = "pip install mediapipe opencv-python  to enable"
        hc_col   = (120, 80, 80)
    _draw_button(surf, _btn('headctrl'), hc_label, 20,
                 hover=head_ctrl.enabled)
    _px_text(surf, hc_desc,
             (cx, _btn('headctrl').bottom + 5), 14, hc_col, center=True)

    # Colorblind toggle — cycles OFF → COLOR-SAFE → MONO
    _CB_LABELS = ["COLORBLIND:  OFF", "COLORBLIND:  COLOR-SAFE", "COLORBLIND:  MONO"]
    _CB_DESCS  = [
        "Normal colours",
        "Yellow / Blue  +  shapes  +  numeric lives",
        "White / Grey  +  shapes  +  numeric lives",
    ]
    _CB_COLS   = [(160, 160, 160), (255, 200, 50), (220, 220, 220)]
    _draw_button(surf, _btn('colorblind'), _CB_LABELS[settings.colorblind_mode], 22,
                 hover=(settings.colorblind_mode > 0))
    _px_text(surf, _CB_DESCS[settings.colorblind_mode],
             (cx, _btn('colorblind').bottom + 6), 15, _CB_COLS[settings.colorblind_mode], center=True)

    _draw_button(surf, _btn('back'), "BACK", 24)
    _px_text(surf, "ESC or SPACE to go back",
             (cx, int(HEIGHT * 0.93)), 17, (120, 120, 120), center=True)


# ── Game over ──────────────────────────────────────────────────────────────────
def _draw_game_over():
    surf = screen.surface
    cx   = WIDTH // 2

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 155))
    surf.blit(overlay, (0, 0))

    panel = pygame.Rect(cx - int(WIDTH * 0.23), int(HEIGHT * 0.12),
                        int(WIDTH * 0.46), int(HEIGHT * 0.76))
    _draw_panel(surf, panel, bg=(14, 5, 5, 225), border=(200, 45, 45), bw=4)

    _px_text(surf, "GAME  OVER",
             (cx, int(HEIGHT * 0.195)), 62, (255, 50, 50),
             shadow_col=(80, 0, 0), center=True)

    _px_text(surf, f"SCORE   {score:07d}",
             (cx, int(HEIGHT * 0.310)), 30, (255, 240, 80), center=True)
    _px_text(surf, f"COINS   {collected_coins:02d}",
             (cx, int(HEIGHT * 0.375)), 24, (255, 210, 50), center=True)

    _px_text(surf, "HIGH  SCORES",
             (cx, int(HEIGHT * 0.440)), 25, (255, 200, 50), center=True)

    for i, s in enumerate(high_scores[:5]):
        col = (255, 240, 80) if i == 0 else (195, 195, 175)
        _px_text(surf, f"# {i+1}   {s:07d}",
                 (cx, int(HEIGHT * 0.503) + i * int(HEIGHT * 0.057)),
                 22, col, center=True)

    _draw_button(surf, _btn('back'), "PLAY  AGAIN", 24)
    _px_text(surf, "SPACE to restart",
             (cx, int(HEIGHT * 0.92)), 18, (140, 140, 140), center=True)


pgzrun.go()
