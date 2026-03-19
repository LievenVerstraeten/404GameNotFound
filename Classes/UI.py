"""
UI — drawing primitives, colour theming, buttons, text, and layout helpers.

Call ui.init() once at startup.
Call ui.begin_frame() once at the start of every draw() call.
"""

import pygame

# ── Module-level state (set once at startup) ──────────────────────────────────
_WIDTH        = 0
_HEIGHT       = 0
_PIXEL_FONT   = None
_fonts: dict  = {}
_vignette_surf = None
_heart_img     = None
_dark_heart_img = None

# ── Per-frame state (set by begin_frame each draw cycle) ──────────────────────
_colorblind_mode  = 0
_hcursor_pos      = None
_click_flash_rects: dict = {}

_CB_ADD = {
    1: (0,   0,  90),
    2: (0,   0,  90),
    3: (90,  0,   0),
}


def init(width, height, pixel_font_path):
    """Call once after pygame is initialised."""
    global _WIDTH, _HEIGHT, _PIXEL_FONT
    _WIDTH      = width
    _HEIGHT     = height
    _PIXEL_FONT = pixel_font_path


def begin_frame(hcursor_pos, click_flash_rects, colorblind_mode):
    """Call at the start of every draw() before rendering any UI."""
    global _hcursor_pos, _click_flash_rects, _colorblind_mode
    _hcursor_pos       = hcursor_pos
    _click_flash_rects = click_flash_rects
    _colorblind_mode   = colorblind_mode


# ── Font ──────────────────────────────────────────────────────────────────────

def font(size):
    """Return a cached pygame font."""
    if size not in _fonts:
        pygame.font.init()
        if _PIXEL_FONT:
            try:
                f = pygame.font.Font(_PIXEL_FONT, size)
                f.render("A", True, (255, 255, 255))
                _fonts[size] = f
            except Exception:
                pass
        if size not in _fonts:
            _fonts[size] = pygame.font.SysFont(None, size)
    return _fonts[size]


def px_text(surf, text, pos, size, color,
            shadow_col=None, center=False, outline=None):
    """Pixel-perfect text with Minecraft-style black outline.
    Returns (text_w, text_h)."""
    f        = font(size)
    rendered = f.render(str(text), True, color)
    rx, ry   = pos
    if center:
        rx -= rendered.get_width()  // 2
        ry -= rendered.get_height() // 2

    ow   = (max(1, size // 40) if outline is None else outline)
    dark = f.render(str(text), True, (0, 0, 0))
    for dx in range(-ow, ow + 1):
        for dy in range(-ow, ow + 1):
            if dx == 0 and dy == 0:
                continue
            surf.blit(dark, (rx + dx, ry + dy))

    surf.blit(rendered, (rx, ry))
    return rendered.get_width(), rendered.get_height()


# ── Colour theming ────────────────────────────────────────────────────────────

def get_ui_colors():
    """Return colour dict for the current colorblind mode."""
    m = _colorblind_mode
    if m == 4:   return {'panel_bg': (15,15,15,215), 'panel_border': (200,200,200), 'btn_bg': (30,30,30,220), 'btn_bord': (150,150,150), 'btn_tcol': (200,200,200), 'btn_hbg': (60,60,60,240), 'btn_hbord': (255,255,255), 'btn_htcol': (255,255,255), 'title_404': (255,255,255), 'title_404_shadow': (100,100,100), 'title_sub': (200,200,200), 'text_main': (220,220,220), 'text_dim': (150,150,150), 'text_highlight': (255,255,255), 'hud_score': (255,255,255), 'hud_progress': (180,180,180), 'hud_border': (200,200,200)}
    elif m in (1,2): return {'panel_bg': (10,25,50,215), 'panel_border': (255,220,50), 'btn_bg': (15,40,80,220), 'btn_bord': (100,150,255), 'btn_tcol': (200,220,255), 'btn_hbg': (30,70,130,240), 'btn_hbord': (180,210,255), 'btn_htcol': (255,255,255), 'title_404': (255,220,50), 'title_404_shadow': (100,80,0), 'title_sub': (100,180,255), 'text_main': (220,220,220), 'text_dim': (150,170,200), 'text_highlight': (255,220,50), 'hud_score': (255,220,50), 'hud_progress': (100,150,255), 'hud_border': (255,220,50)}
    elif m == 3: return {'panel_bg': (20,5,5,215), 'panel_border': (255,70,70), 'btn_bg': (40,10,10,220), 'btn_bord': (200,50,50), 'btn_tcol': (255,150,150), 'btn_hbg': (70,20,20,240), 'btn_hbord': (255,100,100), 'btn_htcol': (255,200,200), 'title_404': (50,255,255), 'title_404_shadow': (0,100,100), 'title_sub': (255,80,80), 'text_main': (220,220,220), 'text_dim': (200,150,150), 'text_highlight': (50,255,255), 'hud_score': (50,255,255), 'hud_progress': (255,80,80), 'hud_border': (50,255,255)}
    else:        return {'panel_bg': (12,12,30,215), 'panel_border': (255,220,50), 'btn_bg': (25,20,5,220), 'btn_bord': (185,152,28), 'btn_tcol': (215,190,75), 'btn_hbg': (55,42,8,240), 'btn_hbord': (255,235,90), 'btn_htcol': (255,248,140), 'title_404': (255,70,70), 'title_404_shadow': (80,0,0), 'title_sub': (255,220,50), 'text_main': (215,215,215), 'text_dim': (140,140,140), 'text_highlight': (90,210,255), 'hud_score': (255,240,80), 'hud_progress': (255,210,40), 'hud_border': (160,130,18)}


def apply_colorblind_filter(surf):
    """Apply the colorblind overlay to surf. Call once per frame after all drawing."""
    mode = _colorblind_mode
    if mode == 0:
        return
    if mode == 4:
        try:
            surf.blit(pygame.transform.grayscale(surf), (0, 0))
        except AttributeError:
            pass
        return
    surf.fill(_CB_ADD[mode], special_flags=pygame.BLEND_RGB_ADD)


# ── Panel / button primitives ─────────────────────────────────────────────────

def draw_pixel_corners(surf, rect, col, size=10):
    """Bright pixel squares at each corner."""
    x0, y0 = rect.left, rect.top
    x1, y1 = rect.right - size, rect.bottom - size
    for px, py in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        pygame.draw.rect(surf, col, (px, py, size, size))


def draw_panel(surf, rect, bg=None, border=None, bw=3):
    c = get_ui_colors()
    if bg is None:     bg     = c['panel_bg']
    if border is None: border = c['panel_border']
    panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    panel.fill(bg)
    surf.blit(panel, rect.topleft)
    pygame.draw.rect(surf, border, rect, bw)
    inner = rect.inflate(-bw * 2 - 2, -bw * 2 - 2)
    hi = tuple(min(255, v + 60) for v in border[:3])
    pygame.draw.rect(surf, hi, inner, 1)
    draw_pixel_corners(surf, rect, hi, size=8)


def draw_button(surf, rect, label, size=24, hover=None):
    """Draw a pixel-art button. hover=None → auto-detect from mouse + head cursor."""
    c      = get_ui_colors()
    mx, my = pygame.mouse.get_pos()
    if not hover:
        hover = rect.collidepoint(mx, my)
        if not hover and _hcursor_pos is not None:
            hover = rect.collidepoint(_hcursor_pos)
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
        sh = tuple(max(0, v - 70) for v in bord[:3])
        pygame.draw.rect(surf, sh, (rect.x + 3, rect.bottom - 5, rect.width - 6, 2))
        px_text(surf, label, (rect.centerx + 1, rect.centery + 2), size, tcol, center=True)
    else:
        hi = tuple(min(255, v + 80) for v in bord[:3])
        pygame.draw.rect(surf, hi, (rect.x + 3, rect.y + 3, rect.width - 6, 2))
        draw_pixel_corners(surf, rect, hi, size=6)
        px_text(surf, label, (rect.centerx, rect.centery), size, tcol, center=True)


def draw_coin_icon(surf, cx, cy, r=9):
    """Draw a tiny pixel-art coin centred at (cx, cy) with radius r."""
    pygame.draw.rect(surf, (200, 140,  0), (cx - r,     cy - r,     r * 2,     r * 2))
    pygame.draw.rect(surf, (255, 210, 40), (cx - r + 2, cy - r + 2, r * 2 - 4, r * 2 - 4))
    pygame.draw.rect(surf, (255, 240,100), (cx - r + 4, cy - r + 4, r * 2 - 8, r * 2 - 8))
    pygame.draw.rect(surf, (140,  95,  0), (cx - r,     cy - r,     r * 2,     r * 2), 2)


# ── Button layout ─────────────────────────────────────────────────────────────

def btn_rect(name):
    """Return the pygame.Rect for a named button."""
    cx  = _WIDTH  // 2
    bw  = int(_WIDTH  * 0.22)
    bh  = int(_HEIGHT * 0.088)
    gap = int(bh * 0.30)
    my  = int(_HEIGHT * 0.42)
    pos = {
        'play':     (cx - bw // 2, my),
        'tutorial': (cx - bw // 2, my +  bh + gap),
        'settings': (cx - bw // 2, my + (bh + gap) * 2),
        'exit':     (cx - bw // 2, my + (bh + gap) * 3),
        'back':     (cx - bw // 2, int(_HEIGHT * 0.84)),
    }

    sbw = int(_WIDTH * 0.50)
    sbh = int(_HEIGHT * 0.078)
    if name == 'headctrl':   return pygame.Rect(cx - sbw // 2, _HEIGHT - int(_HEIGHT * 0.38), sbw, sbh)
    if name == 'colorblind': return pygame.Rect(cx - sbw // 2, _HEIGHT - int(_HEIGHT * 0.27), sbw, sbh)
    if name == 'back':       return pygame.Rect(cx - bw  // 2, _HEIGHT - int(_HEIGHT * 0.16), bw,  bh)

    if name.startswith('go_'):
        go_bw  = int(_WIDTH * 0.16)
        go_gap = int(_WIDTH * 0.015)
        if name == 'go_play':       return pygame.Rect(cx - go_bw - go_gap, int(_HEIGHT * 0.76), go_bw, bh)
        elif name == 'go_settings': return pygame.Rect(cx + go_gap,          int(_HEIGHT * 0.76), go_bw, bh)
        elif name == 'go_menu':     return pygame.Rect(cx - go_bw - go_gap,  int(_HEIGHT * 0.85), go_bw, bh)
        elif name == 'go_exit':     return pygame.Rect(cx + go_gap,           int(_HEIGHT * 0.85), go_bw, bh)

    bx, by = pos.get(name, (0, 0))
    return pygame.Rect(bx, by, bw, bh)


# ── Vignette ──────────────────────────────────────────────────────────────────

def get_vignette():
    """Return cached vignette surface."""
    global _vignette_surf
    if _vignette_surf is None:
        _vignette_surf = pygame.Surface((_WIDTH, _HEIGHT), pygame.SRCALPHA)
        steps = 22
        eh    = int(_HEIGHT * 0.15)
        ew    = int(_WIDTH  * 0.10)
        for i in range(steps):
            t  = i / steps
            h  = max(1, eh // steps + 1)
            wa = max(1, ew // steps + 1)
            a_h = int(95  * (1 - t) ** 2)
            a_w = int(65  * (1 - t) ** 2)
            yt  = int(t * eh)
            yb  = _HEIGHT - 1 - int(t * eh)
            xl  = int(t * ew)
            xr  = _WIDTH  - 1 - int(t * ew)
            pygame.draw.rect(_vignette_surf, (0, 0, 0, a_h), (0,  yt, _WIDTH,  h))
            pygame.draw.rect(_vignette_surf, (0, 0, 0, a_h), (0,  yb, _WIDTH,  h))
            pygame.draw.rect(_vignette_surf, (0, 0, 0, a_w), (xl,  0, wa, _HEIGHT))
            pygame.draw.rect(_vignette_surf, (0, 0, 0, a_w), (xr,  0, wa, _HEIGHT))
    return _vignette_surf


# ── Heart images ──────────────────────────────────────────────────────────────

def load_heart_imgs():
    """Lazily load and cache heart images. Call once per draw() before draw_hud."""
    global _heart_img, _dark_heart_img
    if _heart_img is not None:
        return
    hs = int(_HEIGHT * 0.135)
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


def get_heart_imgs():
    """Return (heart_img, dark_heart_img) — call load_heart_imgs() first."""
    return _heart_img, _dark_heart_img


# ── Head cursor ───────────────────────────────────────────────────────────────

def draw_head_cursor(surf, pos):
    """Draw a pixel-art crosshair at pos (x, y). No-op if pos is None."""
    if pos is None:
        return
    x, y = pos
    c    = get_ui_colors()
    col  = c.get('hud_score', (80, 255, 100))
    arm, gap, w = 13, 5, 2
    for ox, oy in ((1, 1),):
        pygame.draw.line(surf, (0, 0, 0), (x - arm + ox, y + oy), (x - gap + ox, y + oy), w + 1)
        pygame.draw.line(surf, (0, 0, 0), (x + gap + ox, y + oy), (x + arm + ox, y + oy), w + 1)
        pygame.draw.line(surf, (0, 0, 0), (x + ox, y - arm + oy), (x + ox, y - gap + oy), w + 1)
        pygame.draw.line(surf, (0, 0, 0), (x + ox, y + gap + oy), (x + ox, y + arm + oy), w + 1)
    pygame.draw.line(surf, col, (x - arm, y), (x - gap, y), w)
    pygame.draw.line(surf, col, (x + gap, y), (x + arm, y), w)
    pygame.draw.line(surf, col, (x, y - arm), (x, y - gap), w)
    pygame.draw.line(surf, col, (x, y + gap), (x, y + arm), w)
    pygame.draw.circle(surf, (0, 0, 0), (x, y), 3)
    pygame.draw.circle(surf, col,       (x, y), 2)
