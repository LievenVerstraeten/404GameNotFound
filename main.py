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

# ── Button click-flash registry (rect_tuple -> seconds_remaining) ──────────────
_click_flash_rects: dict = {}

# ── Tutorial / Settings scroll ────────────────────────────────────────────────
_tutorial_scroll     = 0.0
_tutorial_max_scroll = 0
_settings_scroll     = 0.0
_settings_max_scroll = 0

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
def get_ui_colors():
    m = settings.colorblind_mode
    if m == 4: return {'panel_bg': (15,15,15,215), 'panel_border': (200,200,200), 'btn_bg': (30,30,30,220), 'btn_bord': (150,150,150), 'btn_tcol': (200,200,200), 'btn_hbg': (60,60,60,240), 'btn_hbord': (255,255,255), 'btn_htcol': (255,255,255), 'title_404': (255,255,255), 'title_404_shadow': (100,100,100), 'title_sub': (200,200,200), 'text_main': (220,220,220), 'text_dim': (150,150,150), 'text_highlight': (255,255,255), 'hud_score': (255,255,255), 'hud_progress': (180,180,180), 'hud_border': (200,200,200)}
    elif m in (1,2): return {'panel_bg': (10,25,50,215), 'panel_border': (255,220,50), 'btn_bg': (15,40,80,220), 'btn_bord': (100,150,255), 'btn_tcol': (200,220,255), 'btn_hbg': (30,70,130,240), 'btn_hbord': (180,210,255), 'btn_htcol': (255,255,255), 'title_404': (255,220,50), 'title_404_shadow': (100,80,0), 'title_sub': (100,180,255), 'text_main': (220,220,220), 'text_dim': (150,170,200), 'text_highlight': (255,220,50), 'hud_score': (255,220,50), 'hud_progress': (100,150,255), 'hud_border': (255,220,50)}
    elif m == 3: return {'panel_bg': (20,5,5,215), 'panel_border': (255,70,70), 'btn_bg': (40,10,10,220), 'btn_bord': (200,50,50), 'btn_tcol': (255,150,150), 'btn_hbg': (70,20,20,240), 'btn_hbord': (255,100,100), 'btn_htcol': (255,200,200), 'title_404': (50,255,255), 'title_404_shadow': (0,100,100), 'title_sub': (255,80,80), 'text_main': (220,220,220), 'text_dim': (200,150,150), 'text_highlight': (50,255,255), 'hud_score': (50,255,255), 'hud_progress': (255,80,80), 'hud_border': (50,255,255)}
    else: return {'panel_bg': (12,12,30,215), 'panel_border': (255,220,50), 'btn_bg': (25,20,5,220), 'btn_bord': (185,152,28), 'btn_tcol': (215,190,75), 'btn_hbg': (55,42,8,240), 'btn_hbord': (255,235,90), 'btn_htcol': (255,248,140), 'title_404': (255,70,70), 'title_404_shadow': (80,0,0), 'title_sub': (255,220,50), 'text_main': (215,215,215), 'text_dim': (140,140,140), 'text_highlight': (90,210,255), 'hud_score': (255,240,80), 'hud_progress': (255,210,40), 'hud_border': (160,130,18)}

# ── Colorblind filter (single SDL fill — zero Python overhead) ─────────────────
# Modes 1-3: one Surface.fill() with BLEND_RGB_ADD per frame.
# SDL executes this in C — costs ~microseconds at any resolution, no allocations.
# Adding to a channel shifts colour pairs that look the same onto an axis the
# user CAN see:
#   Protanopia / Deuteranopia (red-green): +blue  → red→magenta, green→cyan
#   Tritanopia (blue-yellow):              +red   → blue→purple, yellow unchanged
# Mode 4: pygame.transform.grayscale() — also C, also free.
_CB_ADD = {
    1: (0,   0,  90),   # Protanopia
    2: (0,   0,  90),   # Deuteranopia  (same red-green confusion axis)
    3: (90,  0,   0),   # Tritanopia
}


def _apply_colorblind_filter():
    mode = settings.colorblind_mode
    if mode == 0:
        return
    surf = screen.surface
    if mode == 4:
        try:
            surf.blit(pygame.transform.grayscale(surf), (0, 0))
        except AttributeError:
            pass   # skip on older pygame builds — UI colours are already mono-safe
        return
    surf.fill(_CB_ADD[mode], special_flags=pygame.BLEND_RGB_ADD)


def _draw_pixel_corners(surf, rect, col, size=10):
    """Bright pixel squares at each corner — classic pixel-art panel accent."""
    x0, y0 = rect.left, rect.top
    x1, y1 = rect.right - size, rect.bottom - size
    for px, py in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        pygame.draw.rect(surf, col, (px, py, size, size))

def _draw_panel(surf, rect, bg=None, border=None, bw=3):
    c = get_ui_colors()
    if bg is None: bg = c['panel_bg']
    if border is None: border = c['panel_border']
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    panel.fill(bg)
    surf.blit(panel, rect.topleft)
    pygame.draw.rect(surf, border, rect, bw)
    # Inner highlight border (1px inset, half-opacity)
    inner = rect.inflate(-bw * 2 - 2, -bw * 2 - 2)
    hi = tuple(min(255, v + 60) for v in border[:3])
    pygame.draw.rect(surf, hi, inner, 1)
    _draw_pixel_corners(surf, rect, hi, size=8)

def _draw_button(surf, rect, label, size=24, hover=None):
    """Draw a pixel-art button.  hover=None → auto-detect from mouse pos."""
    c       = get_ui_colors()
    mx, my  = pygame.mouse.get_pos()
    if not hover:                          # None or False → auto-detect from mouse
        hover = rect.collidepoint(mx, my)  # True stays True (active/toggle indicator)
    clicked = _click_flash_rects.get((rect.x, rect.y, rect.w, rect.h), 0) > 0

    if clicked:
        bg   = tuple(max(0, v - 50) for v in c['btn_hbg'][:3]) + (255,)
        bord = c['btn_bord']
        tcol = c['btn_tcol']
    elif hover:
        bg   = c['btn_hbg']
        bord = c['btn_hbord']
        tcol = c['btn_htcol']
    else:
        bg   = c['btn_bg']
        bord = c['btn_bord']
        tcol = c['btn_tcol']

    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    panel.fill(bg)
    surf.blit(panel, rect.topleft)
    pygame.draw.rect(surf, bord, rect, 3)

    if clicked:
        # pressed-in: bottom shadow instead of top highlight, text offset down
        sh = tuple(max(0, v - 70) for v in bord[:3])
        pygame.draw.rect(surf, sh, (rect.x + 3, rect.bottom - 5, rect.width - 6, 2))
        _px_text(surf, label, (rect.centerx + 1, rect.centery + 2), size, tcol, center=True)
    else:
        hi = tuple(min(255, v + 80) for v in bord[:3])
        pygame.draw.rect(surf, hi, (rect.x + 3, rect.y + 3, rect.width - 6, 2))
        _draw_pixel_corners(surf, rect, hi, size=6)
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
    bw  = int(WIDTH  * 0.22)
    bh  = int(HEIGHT * 0.088)
    gap = int(bh * 0.30)
    my  = int(HEIGHT * 0.42)
    pos = {
        'play':     (cx - bw // 2, my),
        'tutorial': (cx - bw // 2, my +  bh + gap),
        'settings': (cx - bw // 2, my + (bh + gap) * 2),
        'exit':     (cx - bw // 2, my + (bh + gap) * 3),
        'back':        (cx - bw // 2, int(HEIGHT * 0.84)),  # menu only; settings uses _btn('back') override above
    }

    # Settings-specific buttons — wide, pinned at bottom of full-screen panel
    sbw = int(WIDTH * 0.50)
    sbh = int(HEIGHT * 0.078)
    if name == 'headctrl':   return pygame.Rect(cx - sbw // 2, HEIGHT - int(HEIGHT * 0.38), sbw, sbh)
    if name == 'colorblind': return pygame.Rect(cx - sbw // 2, HEIGHT - int(HEIGHT * 0.27), sbw, sbh)
    if name == 'back':       return pygame.Rect(cx - bw  // 2, HEIGHT - int(HEIGHT * 0.16), bw,  bh)

    if name.startswith('go_'):
        go_bw = int(WIDTH * 0.16)
        go_gap = int(WIDTH * 0.015)
        if name == 'go_play':       return pygame.Rect(cx - go_bw - go_gap, int(HEIGHT * 0.76), go_bw, bh)
        elif name == 'go_settings': return pygame.Rect(cx + go_gap,          int(HEIGHT * 0.76), go_bw, bh)
        elif name == 'go_menu':     return pygame.Rect(cx - go_bw - go_gap,  int(HEIGHT * 0.85), go_bw, bh)
        elif name == 'go_exit':     return pygame.Rect(cx + go_gap,           int(HEIGHT * 0.85), go_bw, bh)

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
            speed_mult = 2.0 if coin_boost_active else 1.0
            boss.fire_player_shot(player.getLane(), speed_mult)


def on_mouse_wheel(dy):
    global _tutorial_scroll, _settings_scroll
    step = 120
    if game_state == "tutorial":
        _tutorial_scroll = max(0.0, min(float(_tutorial_max_scroll), _tutorial_scroll - dy * step))
    elif game_state == "settings":
        _settings_scroll = max(0.0, min(float(_settings_max_scroll), _settings_scroll - dy * step))


def _flash_btn(r):
    """Register a short click-flash for rect r."""
    _click_flash_rects[(r.x, r.y, r.w, r.h)] = 0.18


def on_mouse_down(pos):
    global game_state, _tutorial_scroll, _settings_scroll
    if game_state == "menu":
        if   _btn('play').collidepoint(pos):
            _flash_btn(_btn('play'));     _start_game()
        elif _btn('tutorial').collidepoint(pos):
            _flash_btn(_btn('tutorial')); game_state = "tutorial"; _tutorial_scroll = 0.0
        elif _btn('settings').collidepoint(pos):
            _flash_btn(_btn('settings')); game_state = "settings"; _settings_scroll = 0.0
        elif _btn('exit').collidepoint(pos):
            _flash_btn(_btn('exit'));     sys.exit(0)
    elif game_state == "tutorial":
        _tbw = int(WIDTH * 0.22);  _tbh = int(HEIGHT * 0.088)
        _panel_b = HEIGHT - int(HEIGHT * 0.02)
        _back_y  = _panel_b - int(HEIGHT * 0.10) - int(HEIGHT * 0.015) // 2
        tbr = pygame.Rect(WIDTH // 2 - _tbw // 2, _back_y, _tbw, _tbh)
        if tbr.collidepoint(pos):
            _flash_btn(tbr);  game_state = "menu"
    elif game_state == "settings":
        if   _btn('back').collidepoint(pos):
            _flash_btn(_btn('back'));       game_state = "menu"
        elif _btn('colorblind').collidepoint(pos):
            _flash_btn(_btn('colorblind')); settings.colorblind_mode = (settings.colorblind_mode + 1) % 5
        elif _btn('headctrl').collidepoint(pos) and head_ctrl.available:
            _flash_btn(_btn('headctrl'));   head_ctrl.toggle()
    elif game_state == "game_over":
        if   _btn('go_play').collidepoint(pos):
            _flash_btn(_btn('go_play'));     reset()
        elif _btn('go_menu').collidepoint(pos):
            _flash_btn(_btn('go_menu'));     game_state = "menu"
        elif _btn('go_settings').collidepoint(pos):
            _flash_btn(_btn('go_settings')); game_state = "settings"
        elif _btn('go_exit').collidepoint(pos):
            _flash_btn(_btn('go_exit'));     sys.exit(0)


# ── Core game loop ────────────────────────────────────────────────────────────
def _start_game():
    reset()                    # reset() sets game_state = "playing"


def update(dt):
    global MOVE_OFFSET, SPEED, game_state, score, lives
    global invincible_timer, boost_active, boost_timer, score_multiplier
    global collected_coins, coin_boost_active, coin_boost_timer
    global _hit_flash_timer, game_time
    global _tutorial_scroll, _settings_scroll

    # Tick button click-flash timers
    for _k in list(_click_flash_rects):
        _click_flash_rects[_k] -= dt
        if _click_flash_rects[_k] <= 0:
            del _click_flash_rects[_k]

    # Road always animates so menus have a live background
    SPEED        = settings.BASE_SPEED * (2.0 if coin_boost_active else 1.0)
    MOVE_OFFSET += SPEED * dt * 60   # dt-corrected so speed stays constant at any FPS
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

    _apply_colorblind_filter()


# ── HUD ────────────────────────────────────────────────────────────────────────
def _draw_hud():
    surf = screen.surface
    pad  = int(HEIGHT * 0.018)
    hs   = _heart_img.get_width() if _heart_img else int(HEIGHT * 0.135)
    gap  = int(hs * 0.25)
    c    = get_ui_colors()

    # Score — 3× font size
    _px_text(surf, f"SCORE  {score:07d}", (pad, pad), 102, c['hud_score'])

    # Coin counter + progress bar — all 3× larger
    coin_y = pad + 114
    coin_r = int(HEIGHT * 0.039)
    _draw_coin_icon(surf, pad + coin_r, coin_y + coin_r, coin_r)
    _px_text(surf, f" {collected_coins:02d}/{settings.COIN_BOOST_COST}   UP = BOOST",
             (pad + coin_r * 2 + 4, coin_y), 60, c['hud_score'])

    bar_w  = int(WIDTH * 0.27)
    bar_h  = 15
    bar_y  = coin_y + 72
    fill   = int(bar_w * min(1.0, collected_coins / settings.COIN_BOOST_COST))
    pygame.draw.rect(surf, c['panel_bg'], (pad, bar_y, bar_w, bar_h))
    pygame.draw.rect(surf, c['hud_progress'], (pad, bar_y, fill,  bar_h))
    pygame.draw.rect(surf, c['hud_border'], (pad, bar_y, bar_w, bar_h), 2)

    # Active boost labels — colors vary by accessibility mode
    boost_label_y = bar_y + bar_h + 21
    if   settings.colorblind_mode == 4: key_col, speed_col = (240, 240, 240), (160, 160, 160)
    elif settings.colorblind_mode == 3: key_col, speed_col = (255, 100, 100), ( 80, 255, 255)
    elif settings.colorblind_mode >= 1: key_col, speed_col = (255, 165, 0),   ( 30, 200, 255)
    else:                               key_col, speed_col = (200,  80, 255), ( 80, 210, 255)
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
        if   settings.colorblind_mode == 4: flash.fill((220, 220, 220, a))  # white
        elif settings.colorblind_mode == 3: flash.fill((210,  40,   0, a))  # tritanopia uses red
        elif settings.colorblind_mode >= 1: flash.fill((  0, 120, 210, a))  # blue
        else:                               flash.fill((210,   0,   0, a))  # red
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
    c = get_ui_colors()

    # ── Title card ────────────────────────────────────────────────────────────
    tp = pygame.Rect(cx - int(WIDTH * 0.30), int(HEIGHT * 0.06),
                     int(WIDTH * 0.60), int(HEIGHT * 0.30))
    _draw_panel(surf, tp, bg=c['panel_bg'], border=c['panel_border'], bw=5)

    # "404" — large glitchy red
    _px_text(surf, "404", (cx, int(HEIGHT * 0.155)), 110, c['title_404'],
             shadow_col=c['title_404_shadow'], center=True)

    # Pixel-art divider under 404
    div_y = int(HEIGHT * 0.235)
    div_w = int(WIDTH * 0.26)
    pygame.draw.rect(surf, c['panel_border'], (cx - div_w // 2, div_y, div_w, 3))
    _draw_pixel_corners(surf,
                        pygame.Rect(cx - div_w // 2 - 4, div_y - 4, div_w + 8, 11),
                        c['panel_border'], size=5)

    # "GAME NOT FOUND" subtitle
    _px_text(surf, "GAME  NOT  FOUND", (cx, int(HEIGHT * 0.268)), 34, c['title_sub'],
             center=True)

    # ── Best score badge ──────────────────────────────────────────────────────
    if high_scores:
        badge_w = int(WIDTH * 0.22)
        badge_h = int(HEIGHT * 0.048)
        badge = pygame.Rect(cx - badge_w // 2, int(HEIGHT * 0.355), badge_w, badge_h)
        _draw_panel(surf, badge, bg=(0, 0, 0, 160), border=c['hud_score'], bw=2)
        _px_text(surf, f"BEST  {high_scores[0]:07d}",
                 (cx, badge.centery), 26, c['hud_score'], center=True)

    # ── Buttons ───────────────────────────────────────────────────────────────
    _draw_button(surf, _btn('play'),     "►  PLAY  ◄", 34)
    _draw_button(surf, _btn('tutorial'), "TUTORIAL",   26)
    _draw_button(surf, _btn('settings'), "SETTINGS",   26)
    _draw_button(surf, _btn('exit'),     "EXIT",        26)

    # ── Footer ────────────────────────────────────────────────────────────────
    _px_text(surf, "SPACE  or  click  PLAY  to  start",
             (cx, int(HEIGHT * 0.92)), 22, c['text_dim'], center=True)


# ── Tutorial ───────────────────────────────────────────────────────────────────
def _draw_tutorial():
    global _tutorial_max_scroll
    surf = screen.surface
    cx   = WIDTH // 2
    c    = get_ui_colors()

    ROW_FONT = 63
    ROW_H    = 88
    SEP_H    = 44

    rows = [
        ("MOVE",       "<  >  Arrow Keys  —  Change lane"),
        ("JUMP",       "SPACE  —  Jump   (double jump OK)"),
        ("BOOST",      "UP Arrow  —  Speed x2  costs 10 coins"),
        ("", ""),
        ("COINS",      "Gold coins  ->  +score  +coin count"),
        ("ROCK",       "Small rock  ->  jump over it"),
        ("BOULDER",    "Big boulder  ->  DOUBLE JUMP"),
        ("KEY",        "Boost key  ->  score x3  for 6s"),
        ("", ""),
        ("LIVES",      "3 hearts  —  one lost per crash"),
        ("INVULN",     "Brief flash after each hit"),
        ("DAY/NIGHT",  "World cycles every 60 seconds"),
        ("", ""),
        ("BOSS",       "404 boss appears after 60 seconds"),
        ("DODGE",      "1 and 0 projectiles  —  change lane!"),
        ("SHOOT",      "DOWN / S  —  fire coin at boss"),
        ("BOSS HP",    "2 coin hits = 1 boss heart  (10 total)"),
        ("BOOST SHOT", "Speed boost doubles coin shot speed"),
    ]

    # ── Layout ────────────────────────────────────────────────────────────────
    btn_h      = int(HEIGHT * 0.10)
    btn_gap    = int(HEIGHT * 0.015)
    title_h    = int(HEIGHT * 0.13)
    panel_pad  = int(WIDTH  * 0.02)

    panel = pygame.Rect(panel_pad, int(HEIGHT * 0.01),
                        WIDTH - panel_pad * 2, HEIGHT - int(HEIGHT * 0.02))
    _draw_panel(surf, panel, bg=c['panel_bg'], border=c['panel_border'], bw=5)

    # Title
    title_y = panel.y + int(HEIGHT * 0.04)
    _px_text(surf, "HOW  TO  PLAY", (cx, title_y), 90, c['title_sub'], center=True)

    # Pixel divider under title
    div_y = panel.y + title_h
    pygame.draw.rect(surf, c['panel_border'], (panel.x + 20, div_y, panel.width - 40, 3))

    # Scroll area
    scroll_x = panel.x + int(WIDTH * 0.03)
    scroll_y = div_y + 12
    scroll_w = panel.width - int(WIDTH * 0.06)
    scroll_h = panel.bottom - scroll_y - btn_h - btn_gap - int(HEIGHT * 0.02)

    lx_off = 0
    dx_off = int(WIDTH * 0.24)

    # Compute total content height and max scroll
    content_h = sum(ROW_H if label else SEP_H for label, _ in rows) + ROW_H // 2
    _tutorial_max_scroll = max(0, content_h - scroll_h)

    # Render rows into offscreen surface
    content_surf = pygame.Surface((scroll_w, max(content_h, scroll_h)), pygame.SRCALPHA)
    ty = ROW_H // 4
    for label, desc in rows:
        if not label:
            ty += SEP_H
            # Draw a faint separator line
            pygame.draw.rect(content_surf, (*c['panel_border'][:3], 60),
                             (0, ty - SEP_H // 2, scroll_w, 2))
            continue
        _px_text(content_surf, label, (lx_off, ty), ROW_FONT, c['text_highlight'])
        _px_text(content_surf, desc,  (dx_off, ty), ROW_FONT, c['text_main'])
        ty += ROW_H

    # Clip and blit visible slice
    scroll_int = int(_tutorial_scroll)
    surf.set_clip(pygame.Rect(scroll_x, scroll_y, scroll_w, scroll_h))
    surf.blit(content_surf, (scroll_x, scroll_y),
              pygame.Rect(0, scroll_int, scroll_w, scroll_h))
    surf.set_clip(None)

    # Scrollbar
    if _tutorial_max_scroll > 0:
        sb_w  = 8
        sb_x  = scroll_x + scroll_w + 6
        sb_h  = scroll_h
        thumb_h   = max(40, int(sb_h * scroll_h / content_h))
        thumb_y   = scroll_y + int((sb_h - thumb_h) * _tutorial_scroll / _tutorial_max_scroll)
        pygame.draw.rect(surf, (*c['panel_border'][:3], 60),  (sb_x, scroll_y, sb_w, sb_h))
        pygame.draw.rect(surf, c['panel_border'],              (sb_x, thumb_y,  sb_w, thumb_h))

    # Back button — always visible at bottom
    back_bw = int(WIDTH  * 0.22)
    back_bh = int(HEIGHT * 0.088)
    back_rect = pygame.Rect(cx - back_bw // 2,
                            panel.bottom - btn_h - btn_gap // 2,
                            back_bw, back_bh)
    _draw_button(surf, back_rect, "BACK", 54)
    _px_text(surf, "UP / DOWN to scroll    ESC or SPACE to go back",
             (cx, panel.bottom - int(HEIGHT * 0.008)), 22, c['text_dim'], center=True)


# ── Settings ───────────────────────────────────────────────────────────────────
def _draw_settings():
    global _settings_max_scroll
    surf = screen.surface
    cx   = WIDTH // 2
    c    = get_ui_colors()

    ROW_FONT = 55
    ROW_H    = 76
    SEP_H    = 38

    info_rows = [
        ("Move lane",  "Left / Right Arrow"),
        ("Jump",       "SPACE  —  double jump OK"),
        ("Coin boost", f"UP Arrow  —  costs {settings.COIN_BOOST_COST} coins"),
        ("", ""),
        ("Boost dur.", f"{settings.COIN_BOOST_DURATION:.0f}s  speed x2"),
        ("Key boost",  f"x{settings.BOOST_MULTIPLIER} score  for  {settings.BOOST_DURATION:.0f}s"),
        ("Day cycle",  "60s  per  day / night"),
        ("", ""),
        ("Shoot boss", "DOWN / S  —  fire coin at boss"),
        ("Restart",    "SPACE on Game Over screen"),
    ]

    # ── Layout (mirrors tutorial) ─────────────────────────────────────────────
    panel_pad = int(WIDTH * 0.02)
    title_h   = int(HEIGHT * 0.13)

    panel = pygame.Rect(panel_pad, int(HEIGHT * 0.01),
                        WIDTH - panel_pad * 2, HEIGHT - int(HEIGHT * 0.02))
    _draw_panel(surf, panel, bg=c['panel_bg'], border=c['panel_border'], bw=5)

    # Title
    title_y = panel.y + int(HEIGHT * 0.04)
    _px_text(surf, "SETTINGS", (cx, title_y), 90, c['title_sub'], center=True)

    # Divider
    div_y = panel.y + title_h
    pygame.draw.rect(surf, c['panel_border'], (panel.x + 20, div_y, panel.width - 40, 3))

    # Scroll area
    scroll_x = panel.x + int(WIDTH * 0.03)
    scroll_y = div_y + 12
    scroll_w = panel.width - int(WIDTH * 0.06)
    scroll_h = _btn('headctrl').top - int(HEIGHT * 0.03) - scroll_y

    lx_off = 0
    dx_off = int(WIDTH * 0.22)

    # Compute content height
    content_h = sum(ROW_H if label else SEP_H for label, _ in info_rows) + ROW_H // 4
    _settings_max_scroll = max(0, content_h - scroll_h)

    # Render info rows to offscreen surface
    content_surf = pygame.Surface((scroll_w, max(content_h, scroll_h)), pygame.SRCALPHA)
    ty = ROW_H // 8
    for label, val in info_rows:
        if not label:
            ty += SEP_H
            pygame.draw.rect(content_surf, (*c['panel_border'][:3], 60),
                             (0, ty - SEP_H // 2, scroll_w, 2))
            continue
        _px_text(content_surf, label + ":", (lx_off, ty), ROW_FONT, c['text_highlight'])
        _px_text(content_surf, val,         (dx_off, ty), ROW_FONT, c['text_main'])
        ty += ROW_H

    # Clip and blit
    scroll_int = int(_settings_scroll)
    surf.set_clip(pygame.Rect(scroll_x, scroll_y, scroll_w, scroll_h))
    surf.blit(content_surf, (scroll_x, scroll_y),
              pygame.Rect(0, scroll_int, scroll_w, scroll_h))
    surf.set_clip(None)

    # Scrollbar
    if _settings_max_scroll > 0:
        sb_w = 8
        sb_x = scroll_x + scroll_w + 6
        sb_h = scroll_h
        thumb_h = max(40, int(sb_h * scroll_h / content_h))
        thumb_y = scroll_y + int((sb_h - thumb_h) * _settings_scroll / _settings_max_scroll)
        pygame.draw.rect(surf, (*c['panel_border'][:3], 60), (sb_x, scroll_y, sb_w, sb_h))
        pygame.draw.rect(surf, c['panel_border'],             (sb_x, thumb_y,  sb_w, thumb_h))

    # ── Fixed bottom: HEAD CONTROL, COLORBLIND, BACK ──────────────────────────
    pygame.draw.rect(surf, c['panel_border'],
                     (panel.x + 20, _btn('headctrl').top - int(HEIGHT * 0.025), panel.width - 40, 2))

    if head_ctrl.available:
        hc_label = "HEAD CONTROL:  ON " if head_ctrl.enabled else "HEAD CONTROL:  OFF"
        hc_desc  = ("Lean L/C/R = lane    Nod down = jump    Open mouth = shoot"
                    if head_ctrl.enabled else "Click to enable webcam head tracking")
        hc_col   = (80, 255, 160) if head_ctrl.enabled else c['text_dim']
    else:
        hc_label = "HEAD CONTROL:  N/A"
        hc_desc  = "pip install mediapipe opencv-python  to enable"
        hc_col   = c['title_404']
    _draw_button(surf, _btn('headctrl'), hc_label, 30, hover=head_ctrl.enabled)
    _px_text(surf, hc_desc, (cx, _btn('headctrl').bottom + 8), 22, hc_col, center=True)

    _CB_LABELS = ["COLORBLIND:  OFF", "COLORBLIND:  PROTANOPIA",
                  "COLORBLIND:  DEUTERANOPIA", "COLORBLIND:  TRITANOPIA", "COLORBLIND:  MONO"]
    _CB_DESCS  = ["Normal colours", "Red-blind: Blue/Yellow contrast",
                  "Green-blind: Blue/Yellow contrast", "Blue-blind: Red/Cyan contrast",
                  "White/Grey  +  shapes  +  numeric"]
    cb_col = c['text_highlight'] if settings.colorblind_mode > 0 else c['text_dim']
    _draw_button(surf, _btn('colorblind'), _CB_LABELS[settings.colorblind_mode], 30,
                 hover=(settings.colorblind_mode > 0))
    _px_text(surf, _CB_DESCS[settings.colorblind_mode],
             (cx, _btn('colorblind').bottom + 8), 22, cb_col, center=True)

    _draw_button(surf, _btn('back'), "BACK", 54)
    _px_text(surf, "UP / DOWN to scroll    ESC or SPACE to go back",
             (cx, _btn('back').bottom + int(HEIGHT * 0.012)), 22, c['text_dim'], center=True)


# ── Game over ──────────────────────────────────────────────────────────────────
def _draw_game_over():
    surf = screen.surface
    cx   = WIDTH // 2
    c = get_ui_colors()

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 155))
    surf.blit(overlay, (0, 0))

    panel = pygame.Rect(cx - int(WIDTH * 0.23), int(HEIGHT * 0.12),
                        int(WIDTH * 0.46), int(HEIGHT * 0.76))
    _draw_panel(surf, panel, bg=c['panel_bg'], border=c['title_404'], bw=4)

    _px_text(surf, "GAME  OVER",
             (cx, int(HEIGHT * 0.195)), 62, c['title_404'],
             shadow_col=c['title_404_shadow'], center=True)

    _px_text(surf, f"SCORE   {score:07d}",
             (cx, int(HEIGHT * 0.310)), 30, c['hud_score'], center=True)
    _px_text(surf, f"COINS   {collected_coins:02d}",
             (cx, int(HEIGHT * 0.375)), 24, c['title_sub'], center=True)

    _px_text(surf, "HIGH  SCORES",
             (cx, int(HEIGHT * 0.440)), 25, c['title_sub'], center=True)

    for i, s in enumerate(high_scores[:5]):
        col = c['hud_score'] if i == 0 else c['text_main']
        _px_text(surf, f"# {i+1}   {s:07d}",
                 (cx, int(HEIGHT * 0.490) + i * int(HEIGHT * 0.048)),
                 22, col, center=True)

    _draw_button(surf, _btn('go_play'),     "PLAY AGAIN", 22)
    _draw_button(surf, _btn('go_settings'), "SETTINGS", 22)
    _draw_button(surf, _btn('go_menu'),     "MAIN MENU", 22)
    _draw_button(surf, _btn('go_exit'),     "EXIT GAME", 22)
    _px_text(surf, "SPACE to restart",
             (cx, int(HEIGHT * 0.94)), 18, c['text_dim'], center=True)


pgzrun.go()
