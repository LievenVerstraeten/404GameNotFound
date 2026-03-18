import pygame
import random
from pygame import Rect
import math

# ── Colour helpers ────────────────────────────────────────────────────────────
def _lerp_color(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (int(c1[0] + (c2[0] - c1[0]) * t),
            int(c1[1] + (c2[1] - c1[1]) * t),
            int(c1[2] + (c2[2] - c1[2]) * t))

# Day palette
DAY_SKY_TOP    = (100, 180, 235)
DAY_SKY_BOT    = (170, 215, 250)
DAY_GRASS      = (34,  139,  34)
DAY_GRASS_DARK = (22,  100,  22)
TRACK_DAY      = [(118, 118, 118), (98, 98, 98)]

# Night palette
NIGHT_SKY_TOP    = (8,   10,  35)
NIGHT_SKY_BOT    = (15,  20,  55)
NIGHT_GRASS      = (10,  45,  15)
NIGHT_GRASS_DARK = (6,   28,   8)
TRACK_NIGHT      = [(50,  50,  65), (40,  40,  55)]

CYCLE_DURATION = 60.0   # seconds for full day→night→day cycle
PLAYER_Z       = 345    # z depth of the player (matches EntityManager)

# ── Cloud image paths ─────────────────────────────────────────────────────────
_DAY_CLOUD_PATHS = (
    [f"images/Clouds_white/normal/cloud_shape2_{i}.png"         for i in range(1, 6)] +
    [f"images/Clouds_white/chunky/cloud_shape3_{i}.png"         for i in range(1, 6)] +
    [f"images/Clouds_white/cloud clutters/cloud_shape4_{i}.png" for i in range(1, 6)]
)
_NIGHT_CLOUD_PATHS = (
    [f"images/Clouds_gray/normal/cloud_shape2_{i}.png"          for i in range(1, 6)] +
    [f"images/Clouds_gray/chunky/cloud_shape3_{i}.png"          for i in range(1, 6)] +
    [f"images/Clouds_gray/cloud clutter/cloud_shape5_{i}.png"   for i in range(1, 6)]
)

# ── Tree image paths ─────────────────────────────────────────────────────────
# birch_1..6 for roadsides; middle_lane_tree2..6 for more variety
_TREE_PATHS = (
    [f"images/Trees/birch_{i}.png"              for i in range(1, 7)] +
    [f"images/Trees/middle_lane_tree{i}.png"    for i in range(2, 7)]
)


def _load_images(paths):
    imgs = []
    for p in paths:
        try:
            imgs.append(pygame.image.load(p).convert_alpha())
        except Exception:
            imgs.append(None)
    return imgs


def _load_tree_images(paths):
    """Returns list of {'img': Surface, 'aspect': float} or None on failure."""
    result = []
    for p in paths:
        try:
            img = pygame.image.load(p).convert_alpha()
            aspect = img.get_width() / max(1, img.get_height())
            result.append({'img': img, 'aspect': aspect})
        except Exception:
            result.append(None)
    return result


class Background:
    def __init__(self, HEIGHT, WIDTH):
        self.HEIGHT = HEIGHT
        self.WIDTH  = WIDTH
        self.move_offset     = 0
        self.absolute_offset = 0
        self.prev_offset     = 0
        self.time     = 0.0
        self.day_time = 0.5   # start at midday

        # Cloud images
        self._day_imgs   = _load_images(_DAY_CLOUD_PATHS)
        self._night_imgs = _load_images(_NIGHT_CLOUD_PATHS)

        # Cloud objects
        self.clouds = []
        for _ in range(8):
            self.clouds.append({
                'x':       random.uniform(0, WIDTH),
                'y':       random.uniform(HEIGHT * 0.03, HEIGHT * 0.30),
                'w':       random.randint(90, 210),
                'h':       random.randint(45, 100),
                'speed':   random.uniform(14, 38),
                'img_idx': random.randint(0, 14),
            })

        # Stars
        self.stars = [
            (random.randint(0, WIDTH),
             random.randint(0, int(HEIGHT * 0.37)),
             random.randint(1, 3))
            for _ in range(100)
        ]

        # Birds / bats
        self.creatures = []
        for _ in range(5):
            self.creatures.append({
                'x':     random.uniform(0, WIDTH),
                'y':     random.uniform(HEIGHT * 0.06, HEIGHT * 0.33),
                'speed': random.uniform(50, 105),
                'size':  random.randint(4, 7),
            })

        # ── Side trees (sprite-based, z-scrolling) ──
        self._tree_imgs = _load_tree_images(_TREE_PATHS)
        self._dark_mult_surf = pygame.Surface((1, 1))   # reused scratch surface for darkening
        # 4 trees per side = 8 total, spaced ~700 z units apart — sparse, not cluttered
        TREES_PER_SIDE = 4
        TREE_SPACING   = 3000 // TREES_PER_SIDE  # ~750
        self._side_trees = []
        for side in (-1, 1):
            for i in range(TREES_PER_SIDE):
                self._side_trees.append({
                    'z':        i * TREE_SPACING + random.randint(0, 200),
                    'side':     side,
                    'img_idx':  random.randint(0, len(_TREE_PATHS) - 1),
                    'size_mult': random.uniform(0.85, 1.15),
                })

        # ── Horizon treeline (background, scrolls at parallax speed) ──
        HORIZON_COUNT = 14   # trees spread across the width; more = denser treeline
        self._horizon_trees = []
        for i in range(HORIZON_COUNT):
            self._horizon_trees.append({
                'x':       i * (WIDTH / HORIZON_COUNT) + random.randint(-15, 15),
                'img_idx': random.randint(0, len(_TREE_PATHS) - 1),
                'h_mult':  random.uniform(0.65, 1.25),   # height variation
            })

    # ── day_factor: 0 = full night, 1 = full day ─────────────────────────────
    def _day_factor(self):
        return (math.sin(2 * math.pi * self.day_time - math.pi / 2) + 1) / 2

    # ── update ────────────────────────────────────────────────────────────────
    def update(self, new_offset, dt=1 / 60, ground_speed=0.05):
        if new_offset < self.prev_offset:
            self.absolute_offset += 1
        self.prev_offset  = new_offset
        self.move_offset  = new_offset
        self.time        += dt
        self.day_time     = (self.day_time + dt / CYCLE_DURATION) % 1.0

        # Scroll clouds
        for c in self.clouds:
            c['x'] -= c['speed'] * dt
            if c['x'] + c['w'] < 0:
                c['x']       = self.WIDTH + random.randint(20, 130)
                c['y']       = random.uniform(self.HEIGHT * 0.03, self.HEIGHT * 0.30)
                c['img_idx'] = random.randint(0, 14)

        # Scroll birds / bats
        for b in self.creatures:
            b['x'] -= b['speed'] * dt
            if b['x'] < -20:
                b['x'] = self.WIDTH + random.randint(0, 260)
                b['y'] = random.uniform(self.HEIGHT * 0.06, self.HEIGHT * 0.33)

        # Scroll side trees — same z-speed formula as entities, dt-corrected
        z_step = (3000 / 15) * ground_speed * dt * 60
        for t in self._side_trees:
            t['z'] -= z_step
            if t['z'] < 30:   # tree has passed the camera
                t['z']       += 3000 + random.randint(0, 400)
                t['img_idx']  = random.randint(0, len(_TREE_PATHS) - 1)
                t['size_mult'] = random.uniform(0.85, 1.15)

        # Scroll horizon treeline — slow parallax (far-depth equivalent)
        horizon_px_per_s = ground_speed * 500   # pixels per second; far = slow
        for ht in self._horizon_trees:
            ht['x'] -= horizon_px_per_s * dt
            if ht['x'] < -90:
                ht['x']      += self.WIDTH + 180
                ht['img_idx'] = random.randint(0, len(_TREE_PATHS) - 1)
                ht['h_mult']  = random.uniform(0.65, 1.25)

    # ── draw ──────────────────────────────────────────────────────────────────
    def draw(self, screen):
        hz   = self.HEIGHT * 0.4
        rtw  = self.WIDTH  * 0.1
        rbw  = self.WIDTH  * 0.6
        cx   = self.WIDTH  / 2
        df   = self._day_factor()

        # Sky — smooth multi-stop gradient from top to horizon
        sky_top = _lerp_color(NIGHT_SKY_TOP, DAY_SKY_TOP, df)
        sky_bot = _lerp_color(NIGHT_SKY_BOT, DAY_SKY_BOT, df)
        _SSTEPS = 28
        for _gi in range(_SSTEPS):
            _t   = _gi / _SSTEPS
            _col = _lerp_color(sky_top, sky_bot, _t ** 0.75)
            _y0  = int(_t * hz)
            _y1  = int((_gi + 1) / _SSTEPS * hz) + 1
            pygame.draw.rect(screen.surface, _col, (0, _y0, self.WIDTH, max(1, _y1 - _y0)))

        # Stars
        star_alpha = int(255 * max(0.0, 1.0 - df * 3.0))
        if star_alpha > 8:
            ss = pygame.Surface((self.WIDTH, int(hz)), pygame.SRCALPHA)
            for sx, sy, sz in self.stars:
                pygame.draw.rect(ss, (255, 255, 220, star_alpha), (sx, sy, sz, sz))
            screen.surface.blit(ss, (0, 0))

        # Sun
        sun_alpha = int(255 * min(1.0, df * 2.2))
        if sun_alpha > 8:
            sx0, sy0 = int(self.WIDTH * 0.84), int(self.HEIGHT * 0.07)
            ss = pygame.Surface((64, 64), pygame.SRCALPHA)
            pygame.draw.rect(ss, (255, 230, 60,  sun_alpha), (12, 12, 40, 40))
            pygame.draw.rect(ss, (255, 248, 130, sun_alpha), (18, 18, 28, 28))
            for ang in range(4):
                rx = int(32 + math.cos(math.radians(ang * 90)) * 29)
                ry = int(32 + math.sin(math.radians(ang * 90)) * 29)
                pygame.draw.rect(ss, (255, 230, 60, sun_alpha), (rx - 4, ry - 4, 8, 8))
            screen.surface.blit(ss, (sx0 - 32, sy0 - 32))

        # Moon (crescent)
        moon_alpha = int(255 * min(1.0, (1.0 - df) * 2.5))
        if moon_alpha > 8:
            mx, my = int(self.WIDTH * 0.15), int(self.HEIGHT * 0.08)
            ms = pygame.Surface((56, 56), pygame.SRCALPHA)
            pygame.draw.circle(ms, (235, 235, 200, moon_alpha), (28, 28), 20)
            pygame.draw.circle(ms, (0, 0, 0, moon_alpha), (37, 23), 16)
            screen.surface.blit(ms, (mx - 28, my - 28))

        # Sunset / sunrise glow
        sunset_t = max(0.0, 1.0 - abs(df - 0.5) * 5.5)
        if sunset_t > 0.01:
            glow_h = int(hz * 0.55)
            gs = pygame.Surface((self.WIDTH, glow_h), pygame.SRCALPHA)
            max_a = int(170 * sunset_t)
            for row in range(glow_h):
                t  = 1.0 - row / glow_h
                a  = int(max_a * t * t)
                pygame.draw.line(gs, (255, 115, 30, a), (0, row), (self.WIDTH, row))
            screen.surface.blit(gs, (0, int(hz - glow_h)))

        # Clouds
        self._draw_clouds(screen, df, hz)

        # Birds / bats
        self._draw_creatures(screen, df)

        # Grass — gradient from light (horizon) to dark (near), drawn before horizon trees
        grass_top = _lerp_color(NIGHT_GRASS,      DAY_GRASS,      df)
        grass_bot = _lerp_color(NIGHT_GRASS_DARK, DAY_GRASS_DARK, df)
        grass_h   = self.HEIGHT - int(hz)
        _GSTEPS   = 18
        for _gi in range(_GSTEPS):
            _t   = _gi / _GSTEPS
            _col = _lerp_color(grass_top, grass_bot, _t ** 0.85)
            _y0  = int(hz) + int(_t * grass_h)
            _y1  = int(hz) + int((_gi + 1) / _GSTEPS * grass_h) + 1
            pygame.draw.rect(screen.surface, _col, (0, _y0, self.WIDTH, max(1, _y1 - _y0)))
        # Subtle perspective stripe lines
        _shd = _lerp_color(grass_bot, (0, 0, 0), 0.18)
        for _i in range(3):
            _sy = int(hz + grass_h * (0.10 + _i * 0.30))
            pygame.draw.line(screen.surface, _shd, (0, _sy), (self.WIDTH, _sy), 2)

        # Horizon treeline — sits on the horizon, drawn on top of sky+grass
        self._draw_horizon_trees(screen, hz, df)

        # Horizon fog — semi-transparent sky-colour band centred at the horizon;
        # blends the treeline and the sky/grass seam into a natural haze.
        _fh  = int(hz * 0.30)
        _fog = pygame.Surface((self.WIDTH, _fh * 2), pygame.SRCALPHA)
        for _r in range(_fh * 2):
            _dist = abs(_r - _fh) / max(1, _fh)
            _a    = int(155 * max(0.0, 1.0 - _dist ** 1.35))
            pygame.draw.line(_fog, (*sky_bot, _a), (0, _r), (self.WIDTH, _r))
        screen.surface.blit(_fog, (0, int(hz) - _fh))

        # Far trees — drawn before road so road appears on top at mid distance
        self._draw_side_trees(screen, cx, hz, rtw, rbw, df, far_pass=True)

        # Road segments
        tc = [_lerp_color(TRACK_NIGHT[i], TRACK_DAY[i], df) for i in range(2)]
        segments = 15
        for i in range(segments):
            ds = (i +     self.move_offset) / segments
            de = (i + 1 + self.move_offset) / segments
            if ds >= 1.0: continue
            de = min(de, 1.0)
            ps, pe = ds * ds, de * de
            y1 = hz + (self.HEIGHT - hz) * ps
            y2 = hz + (self.HEIGHT - hz) * pe
            w1 = rtw + (rbw - rtw) * ps
            w2 = rtw + (rbw - rtw) * pe
            pts = [(cx - w1/2, y1), (cx + w1/2, y1),
                   (cx + w2/2, y2), (cx - w2/2, y2)]
            color_idx = (i + self.absolute_offset) % 2
            pygame.draw.polygon(screen.surface, tc[color_idx], pts)

        # Road edges & lane dividers
        edge_col = _lerp_color((75, 70, 38), (230, 220, 140), df)
        div_col  = _lerp_color((75, 75, 95), (240, 240, 180), df)
        for side in (-1, 1):
            pygame.draw.line(screen.surface, edge_col,
                             (cx + side * rtw / 2, int(hz)),
                             (cx + side * rbw / 2, self.HEIGHT), 4)
        for side in (-1, 1):
            pygame.draw.line(screen.surface, div_col,
                             (cx + side * rtw / 6, int(hz)),
                             (cx + side * rbw / 6, self.HEIGHT), 3)

        # Near trees — drawn after road so they appear in front at close range
        self._draw_side_trees(screen, cx, hz, rtw, rbw, df, far_pass=False)

    # ── Cloud drawing ─────────────────────────────────────────────────────────
    def _draw_clouds(self, screen, df, horizon_y):
        use_night = df < 0.5
        imgs = self._night_imgs if use_night else self._day_imgs
        for c in self.clouds:
            if c['y'] > horizon_y:
                continue
            idx    = c['img_idx'] % len(imgs)
            img    = imgs[idx]
            cw, ch = int(c['w']), int(c['h'])
            cx, cy = int(c['x']), int(c['y'])
            if img is not None:
                screen.surface.blit(pygame.transform.scale(img, (cw, ch)), (cx, cy))
            else:
                col = (170, 175, 195) if use_night else (240, 245, 255)
                shd = (140, 148, 168) if use_night else (210, 220, 240)
                pygame.draw.rect(screen.surface, shd, (cx, cy + ch // 3, cw, ch * 2 // 3))
                pygame.draw.rect(screen.surface, col, (cx + cw // 4, cy, cw // 2, ch))

    # ── Bird / bat drawing ────────────────────────────────────────────────────
    def _draw_creatures(self, screen, df):
        for b in self.creatures:
            bx, by, bs = int(b['x']), int(b['y']), b['size']
            if df > 0.35:
                col = (30, 30, 55)
                pygame.draw.line(screen.surface, col, (bx - bs, by), (bx, by - bs // 2), 2)
                pygame.draw.line(screen.surface, col, (bx, by - bs // 2), (bx + bs, by), 2)
            else:
                col = (70, 20, 90)
                pygame.draw.line(screen.surface, col, (bx - bs, by - bs // 2), (bx, by), 2)
                pygame.draw.line(screen.surface, col, (bx, by), (bx + bs, by - bs // 2), 2)

    # ── Horizon treeline ──────────────────────────────────────────────────────
    def _draw_horizon_trees(self, screen, hz, df):
        """Small trees sitting right on the horizon — creates a background forest."""
        base_h = int(self.HEIGHT * 0.11)   # small, far-away size

        for ht in self._horizon_trees:
            tree_data = self._tree_imgs[ht['img_idx'] % len(self._tree_imgs)]
            if tree_data is None:
                continue

            th = max(3, int(base_h * ht['h_mult']))
            tw = max(3, int(th * tree_data['aspect']))
            tx = int(ht['x'])
            ty = int(hz) - th + 4   # roots sit just at/below the horizon line

            scaled = pygame.transform.scale(tree_data['img'], (tw, th))

            # Night darkening (RGB mult — keeps transparency clean)
            if df < 0.85:
                factor = max(0, int(255 * min(1.0, df * 1.2)))
                if self._dark_mult_surf.get_size() != (tw, th):
                    self._dark_mult_surf = pygame.Surface((tw, th))
                self._dark_mult_surf.fill((factor, factor, min(255, factor + 15)))
                scaled.blit(self._dark_mult_surf, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

            screen.surface.blit(scaled, (tx - tw // 2, ty))

    # ── Side tree drawing ─────────────────────────────────────────────────────
    _TREE_FADE_Z = 650   # z below which side trees start fading out

    def _draw_side_trees(self, screen, cx, hz, rtw, rbw, df, far_pass=True):
        """
        far_pass=True  → only draw trees with z > PLAYER_Z  (behind player, before road)
        far_pass=False → only draw trees with z <= PLAYER_Z (in front, after road edges)
        Sorted far→near so nearer trees overlap farther ones correctly.
        """
        trees = sorted(self._side_trees, key=lambda t: t['z'], reverse=True)
        base_h = self.HEIGHT * 0.22   # reference tree height at scale=1

        for t in trees:
            z = t['z']
            if z <= 30:
                continue
            if far_pass and z <= PLAYER_Z:
                continue
            if not far_pass and z > PLAYER_Z:
                continue

            depth = max(0.0, 1.0 - z / 3000.0)
            p     = depth * depth
            scale = 0.2 + p * 1.8

            y_base = int(hz + (self.HEIGHT - hz) * p)
            road_w = rtw + (rbw - rtw) * p

            tree_data = self._tree_imgs[t['img_idx'] % len(self._tree_imgs)]
            if tree_data is None:
                continue

            th = max(4, int(base_h * scale * t['size_mult']))
            tw = max(4, int(th * tree_data['aspect']))

            # Place tree just outside the road edge
            tx = int(cx + t['side'] * (road_w / 2 + tw * 0.45))

            scaled = pygame.transform.scale(tree_data['img'], (tw, th))

            # Night darkening — BLEND_RGB_MULT only touches RGB, alpha stays intact
            if df < 0.85:
                factor = max(0, int(255 * min(1.0, df * 1.2)))
                if self._dark_mult_surf.get_size() != (tw, th):
                    self._dark_mult_surf = pygame.Surface((tw, th))
                self._dark_mult_surf.fill((factor, factor, min(255, factor + 15)))
                scaled.blit(self._dark_mult_surf, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

            # Fade out when close to camera — BLEND_RGBA_MULT multiplies per-pixel
            # alpha so transparent areas remain transparent throughout the fade
            if z < self._TREE_FADE_Z:
                fade_t     = max(0.0, (z - 30) / (self._TREE_FADE_Z - 30))
                fade_alpha = int(255 * fade_t)
                fade_surf  = pygame.Surface((tw, th), pygame.SRCALPHA)
                fade_surf.fill((255, 255, 255, fade_alpha))
                scaled.blit(fade_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

            screen.surface.blit(scaled, (tx - tw // 2, y_base - th))
