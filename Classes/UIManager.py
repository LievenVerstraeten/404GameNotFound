import pygame
import sys

class UIManager:
    def __init__(self, game, width, height, settings):
        self.game = game
        self.width = width
        self.height = height
        self.settings = settings
        
        self.fonts = {}
        self.vignette_surf = None
        self.heart_img = None
        self.dark_heart_img = None

    def get_ui_colors(self):
        m = self.settings.colorblind_mode
        if m == 4: return {'panel_bg': (15,15,15,215), 'panel_border': (200,200,200), 'btn_bg': (30,30,30,220), 'btn_bord': (150,150,150), 'btn_tcol': (200,200,200), 'btn_hbg': (60,60,60,240), 'btn_hbord': (255,255,255), 'btn_htcol': (255,255,255), 'title_404': (255,255,255), 'title_404_shadow': (100,100,100), 'title_sub': (200,200,200), 'text_main': (220,220,220), 'text_dim': (150,150,150), 'text_highlight': (255,255,255), 'hud_score': (255,255,255), 'hud_progress': (180,180,180), 'hud_border': (200,200,200)}
        elif m in (1,2): return {'panel_bg': (10,25,50,215), 'panel_border': (255,220,50), 'btn_bg': (15,40,80,220), 'btn_bord': (100,150,255), 'btn_tcol': (200,220,255), 'btn_hbg': (30,70,130,240), 'btn_hbord': (180,210,255), 'btn_htcol': (255,255,255), 'title_404': (255,220,50), 'title_404_shadow': (100,80,0), 'title_sub': (100,180,255), 'text_main': (220,220,220), 'text_dim': (150,170,200), 'text_highlight': (255,220,50), 'hud_score': (255,220,50), 'hud_progress': (100,150,255), 'hud_border': (255,220,50)}
        elif m == 3: return {'panel_bg': (20,5,5,215), 'panel_border': (255,70,70), 'btn_bg': (40,10,10,220), 'btn_bord': (200,50,50), 'btn_tcol': (255,150,150), 'btn_hbg': (70,20,20,240), 'btn_hbord': (255,100,100), 'btn_htcol': (255,200,200), 'title_404': (50,255,255), 'title_404_shadow': (0,100,100), 'title_sub': (255,80,80), 'text_main': (220,220,220), 'text_dim': (200,150,150), 'text_highlight': (50,255,255), 'hud_score': (50,255,255), 'hud_progress': (255,80,80), 'hud_border': (50,255,255)}
        else: return {'panel_bg': (12,12,30,215), 'panel_border': (255,220,50), 'btn_bg': (25,20,5,220), 'btn_bord': (185,152,28), 'btn_tcol': (215,190,75), 'btn_hbg': (55,42,8,240), 'btn_hbord': (255,235,90), 'btn_htcol': (255,248,140), 'title_404': (255,70,70), 'title_404_shadow': (80,0,0), 'title_sub': (255,220,50), 'text_main': (215,215,215), 'text_dim': (140,140,140), 'text_highlight': (90,210,255), 'hud_score': (255,240,80), 'hud_progress': (255,210,40), 'hud_border': (160,130,18)}

    def get_font(self, size):
        if size not in self.fonts:
            pygame.font.init()
            if self.settings.PIXEL_FONT:
                try:
                    f = pygame.font.Font(self.settings.PIXEL_FONT, size)
                    f.render("A", True, (255, 255, 255))
                    self.fonts[size] = f
                except Exception:
                    pass
            if size not in self.fonts:
                self.fonts[size] = pygame.font.SysFont(None, size)
        return self.fonts[size]

    def px_text(self, surf, text, pos, size, color, shadow_col=None, center=False, outline=None):
        f = self.get_font(size)
        rendered = f.render(str(text), True, color)
        rx, ry = pos
        if center:
            rx -= rendered.get_width() // 2
            ry -= rendered.get_height() // 2

        ow = (max(1, size // 40) if outline is None else outline)
        dark = f.render(str(text), True, (0, 0, 0))
        for dx in range(-ow, ow + 1):
            for dy in range(-ow, ow + 1):
                if dx == 0 and dy == 0: continue
                surf.blit(dark, (rx + dx, ry + dy))
        surf.blit(rendered, (rx, ry))
        return rendered.get_width(), rendered.get_height()

    def draw_panel(self, surf, rect, bg=None, border=None, bw=3):
        c = self.get_ui_colors()
        if bg is None: bg = c['panel_bg']
        if border is None: border = c['panel_border']
        panel = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        panel.fill(bg)
        surf.blit(panel, rect.topleft)
        pygame.draw.rect(surf, border, rect, bw)

    def draw_button(self, surf, rect, label, size=24, hover=False):
        c = self.get_ui_colors()
        bg   = c['btn_hbg'] if hover else c['btn_bg']
        bord = c['btn_hbord'] if hover else c['btn_bord']
        tcol = c['btn_htcol'] if hover else c['btn_tcol']
        self.draw_panel(surf, rect, bg=bg, border=bord, bw=3)
        self.px_text(surf, label, (rect.centerx, rect.centery), size, tcol, center=True)

    def draw_coin_icon(self, surf, cx, cy, r=9):
        pygame.draw.rect(surf, (200, 140,  0), (cx - r,     cy - r,     r * 2,     r * 2))
        pygame.draw.rect(surf, (255, 210, 40), (cx - r + 2, cy - r + 2, r * 2 - 4, r * 2 - 4))
        pygame.draw.rect(surf, (255, 240,100), (cx - r + 4, cy - r + 4, r * 2 - 8, r * 2 - 8))
        pygame.draw.rect(surf, (140,  95,  0), (cx - r,     cy - r,     r * 2,     r * 2), 2)

    def get_btn_rect(self, name):
        cx  = self.width  // 2
        bw  = int(self.width  * 0.17)
        bh  = int(self.height * 0.073)
        gap = int(bh * 0.38)
        my  = int(self.height * 0.42)
        pos = {
            'play':     (cx - bw // 2, my),
            'tutorial': (cx - bw // 2, my +  bh + gap),
            'settings': (cx - bw // 2, my + (bh + gap) * 2),
            'exit':     (cx - bw // 2, my + (bh + gap) * 3),
            'back':        (cx - bw // 2, int(self.height * 0.84)),
            'headctrl':    (cx - bw // 2, int(self.height * 0.63)),
            'colorblind':  (cx - bw // 2, int(self.height * 0.73)),
        }
        if name.startswith('go_'):
            go_bw = int(self.width * 0.16)
            go_gap = int(self.width * 0.015)
            if name == 'go_play':     return pygame.Rect(cx - go_bw - go_gap, int(self.height * 0.76), go_bw, bh)
            elif name == 'go_settings': return pygame.Rect(cx + go_gap, int(self.height * 0.76), go_bw, bh)
            elif name == 'go_menu':   return pygame.Rect(cx - go_bw - go_gap, int(self.height * 0.85), go_bw, bh)
            elif name == 'go_exit':   return pygame.Rect(cx + go_gap, int(self.height * 0.85), go_bw, bh)
        bx, by = pos.get(name, (0, 0))
        return pygame.Rect(bx, by, bw, bh)

    def get_vignette(self):
        if self.vignette_surf is None:
            self.vignette_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            steps = 22
            eh    = int(self.height * 0.15)
            ew    = int(self.width  * 0.10)
            for i in range(steps):
                t  = i / steps
                h  = max(1, eh // steps + 1)
                wa = max(1, ew // steps + 1)
                a_h = int(95  * (1 - t) ** 2)
                a_w = int(65  * (1 - t) ** 2)
                yt  = int(t * eh)
                yb  = self.height - 1 - int(t * eh)
                xl  = int(t * ew)
                xr  = self.width  - 1 - int(t * ew)
                pygame.draw.rect(self.vignette_surf, (0, 0, 0, a_h), (0,  yt, self.width,  h))
                pygame.draw.rect(self.vignette_surf, (0, 0, 0, a_h), (0,  yb, self.width,  h))
                pygame.draw.rect(self.vignette_surf, (0, 0, 0, a_w), (xl,  0, wa, self.height))
                pygame.draw.rect(self.vignette_surf, (0, 0, 0, a_w), (xr,  0, wa, self.height))
        return self.vignette_surf

    def load_heart_imgs(self):
        if self.heart_img is not None: return
        hs = int(self.height * 0.135)
        try:
            raw = pygame.image.load("Images/full_heart.webp").convert_alpha()
        except Exception:
            raw = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.polygon(raw, (220, 30, 30), [(4,10),(10,4),(16,8),(22,4),(28,10),(28,18),(16,30),(4,18)])
        self.heart_img = pygame.transform.scale(raw, (hs, hs))
        self.dark_heart_img = self.heart_img.copy()
        self.dark_heart_img.fill((15, 15, 15, 200), special_flags=pygame.BLEND_RGBA_MULT)

    def draw_hud(self, surf):
        pad = int(self.height * 0.018)
        hs  = self.heart_img.get_width() if self.heart_img else int(self.height * 0.135)
        gap = int(hs * 0.25)
        c   = self.get_ui_colors()

        self.px_text(surf, f"SCORE  {self.game.score:07d}", (pad, pad), 102, c['hud_score'])

        coin_y = pad + 114
        coin_r = int(self.height * 0.039)
        self.draw_coin_icon(surf, pad + coin_r, coin_y + coin_r, coin_r)
        self.px_text(surf, f" {self.game.collected_coins:02d}/{self.settings.COIN_BOOST_COST}   UP = BOOST",
                 (pad + coin_r * 2 + 4, coin_y), 60, c['hud_score'])

        bar_w  = int(self.width * 0.27)
        bar_h  = 15
        bar_y  = coin_y + 72
        fill   = int(bar_w * min(1.0, self.game.collected_coins / self.settings.COIN_BOOST_COST))
        pygame.draw.rect(surf, c['panel_bg'], (pad, bar_y, bar_w, bar_h))
        pygame.draw.rect(surf, c['hud_progress'], (pad, bar_y, fill,  bar_h))
        pygame.draw.rect(surf, c['hud_border'], (pad, bar_y, bar_w, bar_h), 2)

        boost_label_y = bar_y + bar_h + 21
        if   self.settings.colorblind_mode == 4: key_col, speed_col = (240, 240, 240), (160, 160, 160)
        elif self.settings.colorblind_mode == 3: key_col, speed_col = (255, 100, 100), ( 80, 255, 255)
        elif self.settings.colorblind_mode >= 1: key_col, speed_col = (255, 165, 0),   ( 30, 200, 255)
        else:                                    key_col, speed_col = (200,  80, 255), ( 80, 210, 255)
        
        if self.game.boost_active:
            secs = int(self.game.boost_timer) + 1
            self.px_text(surf, f"KEY x{self.game.score_multiplier}  {secs}s", (pad, boost_label_y), 72, key_col)
            boost_label_y += 84
        if self.game.coin_boost_active:
            secs = int(self.game.coin_boost_timer) + 1
            self.px_text(surf, f"SPEED x2  {secs}s", (pad, boost_label_y), 72, speed_col)

        if self.heart_img:
            total_w = self.settings.MAX_LIVES * hs + (self.settings.MAX_LIVES - 1) * gap
            sx      = self.width - total_w - pad
            for i in range(self.settings.MAX_LIVES):
                img = self.heart_img if i < self.game.lives else self.dark_heart_img
                surf.blit(img, (sx + i * (hs + gap), pad))
            if self.settings.colorblind_mode > 0:
                self.px_text(surf, f"LIVES  {self.game.lives}/{self.settings.MAX_LIVES}",
                         (self.width - total_w // 2 - pad, pad + hs + 6),
                         28, (255, 255, 255), center=True)

    def draw_floaters(self, surf):
        for f in self.game.floaters:
            self.px_text(surf, f['text'], (int(f['x']), int(f['y'])), 28, f['color'], center=True)

    def draw_hit_flash(self, surf):
        if self.game.hit_flash_timer > 0:
            a     = int(110 * min(1.0, self.game.hit_flash_timer / (self.settings.INVINCIBLE_DURATION * 0.55)))
            flash = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            if   self.settings.colorblind_mode == 4: flash.fill((220, 220, 220, a))
            elif self.settings.colorblind_mode == 3: flash.fill((210,  40,   0, a))
            elif self.settings.colorblind_mode >= 1: flash.fill((  0, 120, 210, a))
            else:                                    flash.fill((210,   0,   0, a))
            surf.blit(flash, (0, 0))

    def draw_head_preview(self, surf):
        if not self.game.head_ctrl.enabled: return
        frame = self.game.head_ctrl.get_preview_frame()
        if frame is None:
            pw    = int(self.width  * 0.18)
            ph    = int(self.height * 0.07)
            px    = self.width  - pw - int(self.width * 0.012)
            py    = self.height - ph - int(self.height * 0.012)
            badge = pygame.Surface((pw, ph), pygame.SRCALPHA)
            badge.fill((20, 0, 0, 200))
            surf.blit(badge, (px, py))
            msg = self.game.head_ctrl.error_msg or "Opening camera…"
            self.px_text(surf, msg[:38], (px + pw // 2, py + ph // 2), 12, (255, 80, 80), center=True)
            pygame.draw.rect(surf, (180, 0, 0), (px, py, pw, ph), 2)
            return

        try:
            cam_surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        except Exception:
            return

        pw = int(self.width  * 0.20)
        ph = int(pw * frame.shape[0] / frame.shape[1])
        cam_scaled = pygame.transform.scale(cam_surf, (pw, ph))

        margin = int(self.width * 0.012)
        px = self.width  - pw - margin
        py = self.height - ph - margin

        surf.blit(cam_scaled, (px, py))
        border_col = (0, 220, 80) if self.game.head_ctrl.enabled else (200, 50, 50)
        pygame.draw.rect(surf, border_col, (px, py, pw, ph), 3)

    def draw_menu(self, surf):
        cx = self.width // 2
        c = self.get_ui_colors()

        tp = pygame.Rect(cx - int(self.width * 0.27), int(self.height * 0.10),
                         int(self.width * 0.54), int(self.height * 0.24))
        self.draw_panel(surf, tp, bg=c['panel_bg'], border=c['panel_border'], bw=4)
        self.px_text(surf, "404", (cx, int(self.height * 0.165)), 78, c['title_404'], shadow_col=c['title_404_shadow'], center=True)
        self.px_text(surf, "GAME NOT FOUND", (cx, int(self.height * 0.255)), 30, c['title_sub'], center=True)

        if self.game.high_scores:
            self.px_text(surf, f"BEST  {self.game.high_scores[0]:07d}", (cx, int(self.height * 0.325)), 22, c['text_main'], center=True)

        self.draw_button(surf, self.get_btn_rect('play'),     "  PLAY  ",  30)
        self.draw_button(surf, self.get_btn_rect('tutorial'), "TUTORIAL",  24)
        self.draw_button(surf, self.get_btn_rect('settings'), "SETTINGS",  24)
        self.draw_button(surf, self.get_btn_rect('exit'),     "  EXIT  ",  24)

        self.px_text(surf, "SPACE  or  click  PLAY  to  start",
                 (cx, int(self.height * 0.91)), 18, c['text_dim'], center=True)

    def draw_tutorial(self, surf):
        cx   = self.width // 2
        c = self.get_ui_colors()

        panel = pygame.Rect(cx - int(self.width * 0.30), int(self.height * 0.06),
                            int(self.width * 0.60), int(self.height * 0.80))
        self.draw_panel(surf, panel, bg=c['panel_bg'], border=c['panel_border'], bw=4)

        ty = int(self.height * 0.10)
        self.px_text(surf, "HOW  TO  PLAY", (cx, ty), 36, c['title_sub'], center=True)
        ty += int(self.height * 0.08)

        lx = cx - int(self.width * 0.26)
        dx = cx - int(self.width * 0.08)
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
                ty += int(self.height * 0.022);  continue
            self.px_text(surf, label, (lx, ty), 21, c['text_highlight'])
            self.px_text(surf, desc,  (dx, ty), 21, c['text_main'])
            ty += int(self.height * 0.050)

        self.draw_button(surf, self.get_btn_rect('back'), "BACK", 24)
        self.px_text(surf, "ESC or SPACE to go back",
                 (cx, int(self.height * 0.93)), 17, c['text_dim'], center=True)

    def draw_settings(self, surf):
        cx   = self.width // 2
        c = self.get_ui_colors()

        panel = pygame.Rect(cx - int(self.width * 0.26), int(self.height * 0.10),
                            int(self.width * 0.52), int(self.height * 0.65))
        self.draw_panel(surf, panel, bg=c['panel_bg'], border=c['panel_border'], bw=4)

        ty = int(self.height * 0.145)
        self.px_text(surf, "SETTINGS", (cx, ty), 36, c['title_sub'], center=True)
        ty += int(self.height * 0.09)

        lx = cx - int(self.width * 0.22)
        vx = cx + int(self.width * 0.01)
        rows = [
            ("Move lane",    "Left / Right Arrow"),
            ("Jump",         "SPACE   (double jump)"),
            ("Coin boost",   f"UP Arrow  —  costs {self.settings.COIN_BOOST_COST} coins"),
            ("", ""),
            ("Boost dur.",   f"{self.settings.COIN_BOOST_DURATION:.0f}s  speed x2"),
            ("Key boost",    f"x{self.settings.BOOST_MULTIPLIER} score  for  {self.settings.BOOST_DURATION:.0f}s"),
            ("Day cycle",    "60s  per  day / night"),
            ("", ""),
            ("Restart",      "SPACE on Game Over screen"),
        ]
        for label, val in rows:
            if not label:
                ty += int(self.height * 0.022);  continue
            self.px_text(surf, label + ":", (lx, ty), 21, c['text_highlight'])
            self.px_text(surf, val,         (vx, ty), 21, c['text_main'])
            ty += int(self.height * 0.053)

        hc = self.game.head_ctrl
        if hc.available:
            hc_label = "HEAD CONTROL:  ON " if hc.enabled else "HEAD CONTROL:  OFF"
            hc_desc  = ("Nod L/R = lane    Nod down = jump    Open mouth = shoot" if hc.enabled else "Click to enable webcam head tracking")
            hc_col   = (80, 255, 160) if hc.enabled else c['text_dim']
        else:
            hc_label = "HEAD CONTROL:  N/A"
            hc_desc  = "pip install mediapipe opencv-python  to enable"
            hc_col   = c['title_404']
            
        self.draw_button(surf, self.get_btn_rect('headctrl'), hc_label, 20, hover=hc.enabled)
        self.px_text(surf, hc_desc, (cx, self.get_btn_rect('headctrl').bottom + 5), 14, hc_col, center=True)

        _CB_LABELS = ["COLORBLIND:  OFF", "COLORBLIND:  PROTANOPIA", "COLORBLIND:  DEUTERANOPIA", "COLORBLIND:  TRITANOPIA", "COLORBLIND:  MONO"]
        _CB_DESCS  = ["Normal colours", "Red-blind: Blue/Yellow contrast", "Green-blind: Blue/Yellow contrast", "Blue-blind: Red/Cyan contrast", "White/Grey  +  shapes  +  numeric"]
        
        cb_desc_col = c['text_highlight'] if self.settings.colorblind_mode > 0 else c['text_dim']
        self.draw_button(surf, self.get_btn_rect('colorblind'), _CB_LABELS[self.settings.colorblind_mode], 22, hover=(self.settings.colorblind_mode > 0))
        self.px_text(surf, _CB_DESCS[self.settings.colorblind_mode], (cx, self.get_btn_rect('colorblind').bottom + 6), 15, cb_desc_col, center=True)

        self.draw_button(surf, self.get_btn_rect('back'), "BACK", 24)
        self.px_text(surf, "ESC or SPACE to go back",
                 (cx, int(self.height * 0.93)), 17, c['text_dim'], center=True)

    def draw_game_over(self, surf):
        cx   = self.width // 2
        c = self.get_ui_colors()

        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 155))
        surf.blit(overlay, (0, 0))

        panel = pygame.Rect(cx - int(self.width * 0.23), int(self.height * 0.12),
                            int(self.width * 0.46), int(self.height * 0.76))
        self.draw_panel(surf, panel, bg=c['panel_bg'], border=c['title_404'], bw=4)

        self.px_text(surf, "GAME  OVER", (cx, int(self.height * 0.195)), 62, c['title_404'], shadow_col=c['title_404_shadow'], center=True)
        self.px_text(surf, f"SCORE   {self.game.score:07d}", (cx, int(self.height * 0.310)), 30, c['hud_score'], center=True)
        self.px_text(surf, f"COINS   {self.game.collected_coins:02d}", (cx, int(self.height * 0.375)), 24, c['title_sub'], center=True)
        self.px_text(surf, "HIGH  SCORES", (cx, int(self.height * 0.440)), 25, c['title_sub'], center=True)

        for i, s in enumerate(self.game.high_scores[:5]):
            col = c['hud_score'] if i == 0 else c['text_main']
            self.px_text(surf, f"# {i+1}   {s:07d}", (cx, int(self.height * 0.490) + i * int(self.height * 0.048)), 22, col, center=True)

        self.draw_button(surf, self.get_btn_rect('go_play'),     "PLAY AGAIN", 22)
        self.draw_button(surf, self.get_btn_rect('go_settings'), "SETTINGS", 22)
        self.draw_button(surf, self.get_btn_rect('go_menu'),     "MAIN MENU", 22)
        self.draw_button(surf, self.get_btn_rect('go_exit'),     "EXIT GAME", 22)
        self.px_text(surf, "SPACE to restart", (cx, int(self.height * 0.94)), 18, c['text_dim'], center=True)

    def draw_all(self, screen):
        self.load_heart_imgs()
        surf = getattr(screen, 'surface', screen)
        
        screen.clear()
        self.game.road.draw(screen)

        if self.game.game_state == "playing":
            self.game.boss.draw(screen, self.px_text, self.get_font, self.settings.colorblind_mode)
            self.game.entityManager.draw_bg(screen, 345, self.settings.colorblind_mode)
            self.game.player.draw(screen)
            self.game.entityManager.draw_fg(screen, 345, self.settings.colorblind_mode)
            surf.blit(self.get_vignette(), (0, 0))
            self.draw_floaters(surf)
            self.draw_hit_flash(surf)
            self.draw_hud(surf)
            self.draw_head_preview(surf)

        elif self.game.game_state == "game_over":
            self.game.boss.draw(screen, self.px_text, self.get_font, self.settings.colorblind_mode)
            self.game.entityManager.draw_bg(screen, 345, self.settings.colorblind_mode)
            self.game.player.draw(screen)
            self.game.entityManager.draw_fg(screen, 345, self.settings.colorblind_mode)
            surf.blit(self.get_vignette(), (0, 0))
            self.draw_game_over(surf)

        elif self.game.game_state == "menu":
            surf.blit(self.get_vignette(), (0, 0))
            self.draw_menu(surf)

        elif self.game.game_state == "tutorial":
            surf.blit(self.get_vignette(), (0, 0))
            self.draw_tutorial(surf)

        elif self.game.game_state == "settings":
            surf.blit(self.get_vignette(), (0, 0))
            self.draw_settings(surf)

    def handle_click(self, pos):
        state = self.game.game_state
        if state == "menu":
            if   self.get_btn_rect('play').collidepoint(pos):     self.game.start_game()
            elif self.get_btn_rect('tutorial').collidepoint(pos): self.game.game_state = "tutorial"
            elif self.get_btn_rect('settings').collidepoint(pos): self.game.game_state = "settings"
            elif self.get_btn_rect('exit').collidepoint(pos):     sys.exit(0)
        elif state == "tutorial":
            if self.get_btn_rect('back').collidepoint(pos):       self.game.game_state = "menu"
        elif state == "settings":
            if   self.get_btn_rect('back').collidepoint(pos):       self.game.game_state = "menu"
            elif self.get_btn_rect('colorblind').collidepoint(pos): self.settings.colorblind_mode = (self.settings.colorblind_mode + 1) % 5
            elif self.get_btn_rect('headctrl').collidepoint(pos) and self.game.head_ctrl.available:
                self.game.head_ctrl.toggle()
        elif state == "game_over":
            if self.get_btn_rect('go_play').collidepoint(pos):       self.game.reset()
            elif self.get_btn_rect('go_menu').collidepoint(pos):     self.game.game_state = "menu"
            elif self.get_btn_rect('go_settings').collidepoint(pos): self.game.game_state = "settings"
            elif self.get_btn_rect('go_exit').collidepoint(pos):     sys.exit(0)
