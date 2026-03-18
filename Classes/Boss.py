import pygame
import random
import math


class Boss:
    """
    The 404 boss that rises from the horizon after 60 seconds.
    - Floats above the road, pulsing with a purple glow
    - Shoots '1' and '0' pixel projectiles at player lanes
    - Damaged by player coin shots (2 hits = 1 HP)
    - 10 HP total
    """

    MAX_HP       = 10
    BOSS_Z       = 2500      # world-z the boss sits at (far = high z)
    PLAYER_Z     = 345       # world-z of the player
    MAX_Z        = 3000      # same as EntityManager

    def __init__(self, HEIGHT, WIDTH):
        self.HEIGHT = HEIGHT
        self.WIDTH  = WIDTH
        self.active   = False
        self.defeated = False
        self.hp        = self.MAX_HP
        self.coin_hits = 0          # 2 coin hits → lose 1 HP

        self.appear_timer = 0.0     # 0 → FADE_IN; drives alpha fade-in
        self.defeat_timer = 0.0     # counts up after defeat for fade-out
        self.bob_phase    = 0.0     # vertical oscillation
        self.shoot_timer  = 2.5     # countdown to next shot

        self.projectiles  = []      # {'lane', 'z', 'char', 'speed'}
        self.player_shots = []      # {'lane', 'z', 'speed'}

    # ── Public API ────────────────────────────────────────────────────────────

    def activate(self):
        self.active       = True
        self.defeated     = False
        self.hp           = self.MAX_HP
        self.coin_hits    = 0
        self.appear_timer = 0.0
        self.defeat_timer = 0.0
        self.bob_phase    = 0.0
        self.shoot_timer  = 2.5
        self.projectiles.clear()
        self.player_shots.clear()

    def reset(self):
        self.active       = False
        self.defeated     = False
        self.hp           = self.MAX_HP
        self.coin_hits    = 0
        self.appear_timer = 0.0
        self.defeat_timer = 0.0
        self.projectiles.clear()
        self.player_shots.clear()

    def fire_player_shot(self, player_lane, speed_multiplier=1.0):
        """Called when the player presses DOWN / S."""
        if not self.active or self.defeated:
            return
        self.player_shots.append({
            'lane':  player_lane,
            'z':     self.PLAYER_Z + 80.0,   # start just ahead of player
            'speed': 1400.0 * speed_multiplier,
        })

    def update(self, dt, player_lane, is_invincible, is_jumping=False):
        """
        Returns one of: 'player_hit' | 'boss_defeated' | None
        Call every frame while game_state == 'playing'.
        """
        if not self.active:
            return None

        self.appear_timer += dt
        self.bob_phase    += dt * 1.1

        if self.defeated:
            self.defeat_timer += dt
            if self.defeat_timer >= 1.5:   # fade finished — go fully invisible
                self.active = False
            return None

        # ── Boss shoots projectiles ──
        rage          = (self.MAX_HP - self.hp) / self.MAX_HP    # 0→1 as HP drops
        shoot_interval = max(0.65, 2.0 - rage * 1.3)
        self.shoot_timer -= dt
        if self.shoot_timer <= 0 and self.appear_timer > 1.5:
            self.shoot_timer = shoot_interval + random.uniform(-0.15, 0.25)
            lane = player_lane if random.random() < 0.62 else random.randint(0, 2)
            char  = random.choice(['1', '0'])
            speed = 600.0 + rage * 400.0
            self.projectiles.append({
                'lane': lane, 'z': float(self.BOSS_Z - 100),
                'char': char, 'speed': speed,
            })

        # ── Move boss projectiles toward player ──
        result = None
        kept = []
        for p in self.projectiles:
            p['z'] -= p['speed'] * dt
            if p['z'] < self.PLAYER_Z + 90 and p['z'] > self.PLAYER_Z - 60:
                if p['lane'] == player_lane and not is_invincible and not is_jumping:
                    result = 'player_hit'
                    continue             # projectile consumed on hit
            if p['z'] > 0:
                kept.append(p)
        self.projectiles = kept

        # ── Move player shots toward boss ──
        kept_shots = []
        for s in self.player_shots:
            s['z'] += s['speed'] * dt
            if s['z'] >= self.BOSS_Z - 150:
                self.coin_hits += 1
                if self.coin_hits >= 2:
                    self.coin_hits = 0
                    self.hp -= 1
                    if self.hp <= 0:
                        self.hp       = 0
                        self.defeated = True
                        # Immediately clear all in-flight attacks
                        self.projectiles.clear()
                        self.player_shots.clear()
                        result = 'boss_defeated'
                continue                 # shot consumed
            kept_shots.append(s)
        self.player_shots = kept_shots

        return result

    # ── Drawing ───────────────────────────────────────────────────────────────

    def draw(self, screen, px_text_fn, font_fn, colorblind=False):
        if not self.active:
            return
        surf = screen.surface

        if self.defeated:
            # Fade out over 1.5 s then update() sets active=False
            alpha = max(0, int(255 * (1.0 - self.defeat_timer / 1.5)))
        else:
            alpha = min(255, int(255 * self.appear_timer / 1.5))
        hz       = self.HEIGHT * 0.4
        cx       = self.WIDTH  / 2
        bob      = math.sin(self.bob_phase) * 10
        rage     = (self.MAX_HP - self.hp) / self.MAX_HP

        # ── 404 text ──────────────────────────────────────────────────────────
        text_sz = int(self.HEIGHT * (0.15 + rage * 0.04))
        f       = font_fn(text_sz)
        col_r   = min(255, int(180 + rage * 75))
        col_g   = max(0,   int(30  - rage * 30))
        txt_col = (col_r, col_g, int(220 * (1.0 - rage * 0.6)))

        label   = f.render("404", True, txt_col)
        tw, th  = label.get_width(), label.get_height()
        bx      = int(cx - tw // 2)
        by      = int(hz * 0.58 + bob) - th // 2

        # Animated glow rectangle
        pad     = int(self.HEIGHT * 0.018)
        flicker = abs(math.sin(self.bob_phase * 2.5))
        gr_a    = min(alpha, int(140 + flicker * 50))
        gw, gh  = tw + pad * 2, th + pad * 2
        gsurf   = pygame.Surface((gw, gh), pygame.SRCALPHA)
        gsurf.fill((int(25 + flicker * 20), 0, int(35 + flicker * 25), gr_a))
        surf.blit(gsurf, (bx - pad, by - pad))
        bord_a  = min(alpha, 255)
        bord_col = (int(180 * flicker + 60), 0, 255)
        pygame.draw.rect(surf, bord_col, (bx - pad, by - pad, gw, gh), 4)
        # Extra outer glow pass
        pygame.draw.rect(surf, (*bord_col, min(bord_a, 80)),
                         (bx - pad - 4, by - pad - 4, gw + 8, gh + 8), 2)

        # 8-direction black outline then colored "404"
        dark = f.render("404", True, (0, 0, 0))
        ow = 3
        for ddx in range(-ow, ow + 1):
            for ddy in range(-ow, ow + 1):
                if ddx == 0 and ddy == 0:
                    continue
                ds = dark.copy(); ds.set_alpha(alpha)
                surf.blit(ds, (bx + ddx, by + ddy))
        label.set_alpha(alpha)
        surf.blit(label, (bx, by))

        # ── HP bar ────────────────────────────────────────────────────────────
        bar_w  = max(tw, int(tw * 1.2))
        bar_h  = max(10, int(self.HEIGHT * 0.016))
        bar_x  = int(cx - bar_w // 2)
        bar_y  = by + th + int(self.HEIGHT * 0.012)
        hp_frac = self.hp / self.MAX_HP

        bg = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        bg.fill((30, 0, 15, min(alpha, 200)))
        surf.blit(bg, (bar_x, bar_y))

        fill_w = max(0, int(bar_w * hp_frac))
        if fill_w > 0:
            fc = pygame.Surface((fill_w, bar_h), pygame.SRCALPHA)
            fill_color = (
                min(255, int(255 * (1.0 - hp_frac * 0.5))),
                min(255, int(180 * hp_frac)),
                0, min(alpha, 230),
            )
            fc.fill(fill_color)
            surf.blit(fc, (bar_x, bar_y))

        pygame.draw.rect(surf, (*bord_col, min(alpha, 255)),
                         (bar_x, bar_y, bar_w, bar_h), 3)

        hp_label_y = bar_y + bar_h + 4
        px_text_fn(surf, f"HP  {self.hp}/{self.MAX_HP}",
                   (int(cx), hp_label_y),
                   max(14, int(self.HEIGHT * 0.020)),
                   (255, 100, 255), center=True)

        # ── Boss projectiles ──────────────────────────────────────────────────
        for p in sorted(self.projectiles, key=lambda x: x['z'], reverse=True):
            py, pscale, pp = self._project(p['z'])
            px = self._lane_x(p['lane'], pp)
            sz  = max(16, int(self.HEIGHT * 0.085 * pscale))
            pf  = font_fn(sz)

            is_one = p['char'] == '1'
            if   colorblind == 2:  # monochrome: white "1", gray "0"
                pc = (240, 240, 240) if is_one else (140, 140, 140)
            elif colorblind == 1:  # color-safe: yellow "1", blue "0"
                pc = (255, 220,   0) if is_one else ( 30, 100, 255)
            else:                  # default: red "1", cyan "0"
                pc = (255,  60,  60) if is_one else ( 60, 200, 255)

            ps  = pf.render(p['char'], True, pc)
            dk  = pf.render(p['char'], True, (0, 0, 0))
            ox, oy = int(px - ps.get_width() // 2), int(py - ps.get_height() // 2)
            for ddx, ddy in [(-2,0),(2,0),(0,-2),(0,2),(-2,-2),(2,-2),(-2,2),(2,2)]:
                surf.blit(dk, (ox + ddx, oy + ddy))
            surf.blit(ps, (ox, oy))

            # Shape markers in both accessibility modes
            if colorblind > 0:
                mk_sz = max(6, int(sz * 0.38))
                mk_x, mk_y = int(px), oy - mk_sz - 4
                mk_col1 = (240, 240, 240) if colorblind == 2 else (255, 220,   0)
                mk_col0 = (160, 160, 160) if colorblind == 2 else ( 30, 100, 255)
                if is_one:
                    # ▲ triangle
                    pts = [(mk_x, mk_y), (mk_x - mk_sz, mk_y + mk_sz),
                           (mk_x + mk_sz, mk_y + mk_sz)]
                    pygame.draw.polygon(surf, (0, 0, 0),
                                        [(x+2, y+2) for x, y in pts])
                    pygame.draw.polygon(surf, mk_col1, pts)
                else:
                    # ■ square
                    pygame.draw.rect(surf, (0, 0, 0),
                                     (mk_x - mk_sz - 2, mk_y - 2, mk_sz*2+4, mk_sz+4))
                    pygame.draw.rect(surf, mk_col0,
                                     (mk_x - mk_sz, mk_y, mk_sz*2, mk_sz))

        # ── Player coin shots (moving away = shrinking) ───────────────────────
        for s in self.player_shots:
            sy, sscale, sp = self._project(s['z'])
            sx = self._lane_x(s['lane'], sp)
            r   = max(3, int(18 * sscale))
            pygame.draw.rect(surf, (200, 140,  0), (int(sx-r),   int(sy-r),   r*2,   r*2))
            pygame.draw.rect(surf, (255, 210, 40), (int(sx-r+2), int(sy-r+2), r*2-4, r*2-4))
            pygame.draw.rect(surf, (140,  95,  0), (int(sx-r),   int(sy-r),   r*2,   r*2), 2)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _project(self, z):
        hz    = self.HEIGHT * 0.4
        depth = max(0.0, 1.0 - z / self.MAX_Z)
        p     = depth * depth
        y     = hz + (self.HEIGHT - hz) * p
        scale = 0.2 + p * 1.8
        return y, scale, p

    def _lane_x(self, lane, p):
        rtw = self.WIDTH * 0.1
        rbw = self.WIDTH * 0.6
        rw  = rtw + (rbw - rtw) * p
        return self.WIDTH / 2 + (lane - 1) * (rw / 3)
