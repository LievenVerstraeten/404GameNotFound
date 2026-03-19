"""
Screens — all screen and HUD renderers for 404GameNotFound.

Usage:
    renderer = ScreenRenderer(WIDTH, HEIGHT, settings)
    renderer.draw_menu(surf, high_scores)
    ...
"""

import pygame
import Classes.UI as ui


class ScreenRenderer:

    def __init__(self, width, height, settings):
        self._w = width
        self._h = height
        self._s = settings

    # ── HUD ──────────────────────────────────────────────────────────────────

    def draw_hud(self, surf, lives, score, score_multiplier,
                 boost_active, boost_timer, coin_boost_active, coin_boost_timer,
                 collected_coins, invincible_timer, boss):
        pad  = int(self._h * 0.018)
        heart_img, dark_heart_img = ui.get_heart_imgs()
        hs   = heart_img.get_width() if heart_img else int(self._h * 0.135)
        gap  = int(hs * 0.25)
        c    = ui.get_ui_colors()

        ui.px_text(surf, f"SCORE  {score:07d}", (pad, pad), 102, c['hud_score'])

        coin_y = pad + 114
        coin_r = int(self._h * 0.039)
        ui.draw_coin_icon(surf, pad + coin_r, coin_y + coin_r, coin_r)
        ui.px_text(surf, f" {collected_coins:02d}/{self._s.COIN_BOOST_COST}   UP = BOOST",
                   (pad + coin_r * 2 + 4, coin_y), 60, c['hud_score'])

        bar_w  = int(self._w * 0.27)
        bar_h  = 15
        bar_y  = coin_y + 72
        fill   = int(bar_w * min(1.0, collected_coins / self._s.COIN_BOOST_COST))
        pygame.draw.rect(surf, c['panel_bg'], (pad, bar_y, bar_w, bar_h))
        pygame.draw.rect(surf, c['hud_progress'], (pad, bar_y, fill,  bar_h))
        pygame.draw.rect(surf, c['hud_border'], (pad, bar_y, bar_w, bar_h), 2)

        boost_label_y = bar_y + bar_h + 21
        if   self._s.colorblind_mode == 4: key_col, speed_col = (240, 240, 240), (160, 160, 160)
        elif self._s.colorblind_mode == 3: key_col, speed_col = (255, 100, 100), ( 80, 255, 255)
        elif self._s.colorblind_mode >= 1: key_col, speed_col = (255, 165, 0),   ( 30, 200, 255)
        else:                              key_col, speed_col = (200,  80, 255), ( 80, 210, 255)
        if boost_active:
            secs = int(boost_timer) + 1
            ui.px_text(surf, f"KEY x{score_multiplier}  {secs}s",
                       (pad, boost_label_y), 72, key_col)
            boost_label_y += 84
        if coin_boost_active:
            secs = int(coin_boost_timer) + 1
            ui.px_text(surf, f"SPEED x2  {secs}s",
                       (pad, boost_label_y), 72, speed_col)

        if heart_img:
            total_w = self._s.MAX_LIVES * hs + (self._s.MAX_LIVES - 1) * gap
            sx      = self._w - total_w - pad
            for i in range(self._s.MAX_LIVES):
                img = heart_img if i < lives else dark_heart_img
                surf.blit(img, (sx + i * (hs + gap), pad))
            if self._s.colorblind_mode > 0:
                ui.px_text(surf, f"LIVES  {lives}/{self._s.MAX_LIVES}",
                           (self._w - total_w // 2 - pad, pad + hs + 6),
                           28, (255, 255, 255), center=True)

    # ── Floaters ─────────────────────────────────────────────────────────────

    def draw_floaters(self, surf, floaters):
        for f in floaters:
            ui.px_text(surf, f['text'],
                       (int(f['x']), int(f['y'])), 28, f['color'], center=True)

    # ── Hit flash ─────────────────────────────────────────────────────────────

    def draw_hit_flash(self, surf, hit_flash_timer):
        if hit_flash_timer > 0:
            a     = int(110 * min(1.0, hit_flash_timer / (self._s.INVINCIBLE_DURATION * 0.55)))
            flash = pygame.Surface((self._w, self._h), pygame.SRCALPHA)
            if   self._s.colorblind_mode == 4: flash.fill((220, 220, 220, a))
            elif self._s.colorblind_mode == 3: flash.fill((210,  40,   0, a))
            elif self._s.colorblind_mode >= 1: flash.fill((  0, 120, 210, a))
            else:                              flash.fill((210,   0,   0, a))
            surf.blit(flash, (0, 0))

    # ── Head preview ──────────────────────────────────────────────────────────

    def draw_head_preview(self, surf, head_ctrl):
        """Blit the live annotated webcam frame to the bottom-right corner."""
        if not head_ctrl.enabled:
            return
        frame = head_ctrl.get_preview_frame()
        if frame is None:
            pw    = int(self._w  * 0.18)
            ph    = int(self._h * 0.07)
            px    = self._w  - pw - int(self._w * 0.012)
            py    = self._h - ph - int(self._h * 0.012)
            badge = pygame.Surface((pw, ph), pygame.SRCALPHA)
            badge.fill((20, 0, 0, 200))
            surf.blit(badge, (px, py))
            msg = head_ctrl.error_msg or "Opening camera…"
            ui.px_text(surf, msg[:38], (px + pw // 2, py + ph // 2),
                       12, (255, 80, 80), center=True)
            pygame.draw.rect(surf, (180, 0, 0), (px, py, pw, ph), 2)
            return

        try:
            cam_surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1))
        except Exception:
            return

        pw = int(self._w  * 0.20)
        ph = int(pw * frame.shape[0] / frame.shape[1])
        cam_scaled = pygame.transform.scale(cam_surf, (pw, ph))

        margin = int(self._w * 0.012)
        px = self._w  - pw - margin
        py = self._h - ph - margin

        surf.blit(cam_scaled, (px, py))
        border_col = (0, 220, 80) if head_ctrl.enabled else (200, 50, 50)
        pygame.draw.rect(surf, border_col, (px, py, pw, ph), 3)

    # ── Menu ─────────────────────────────────────────────────────────────────

    def draw_menu(self, surf, high_scores):
        cx = self._w // 2
        c  = ui.get_ui_colors()

        tp = pygame.Rect(cx - int(self._w * 0.30), int(self._h * 0.06),
                         int(self._w * 0.60), int(self._h * 0.30))
        ui.draw_panel(surf, tp, bg=c['panel_bg'], border=c['panel_border'], bw=5)

        ui.px_text(surf, "404", (cx, int(self._h * 0.155)), 110, c['title_404'],
                   shadow_col=c['title_404_shadow'], center=True)

        div_y = int(self._h * 0.235)
        div_w = int(self._w * 0.26)
        pygame.draw.rect(surf, c['panel_border'], (cx - div_w // 2, div_y, div_w, 3))
        ui.draw_pixel_corners(surf,
                              pygame.Rect(cx - div_w // 2 - 4, div_y - 4, div_w + 8, 11),
                              c['panel_border'], size=5)

        ui.px_text(surf, "GAME  NOT  FOUND", (cx, int(self._h * 0.268)), 34, c['title_sub'],
                   center=True)

        if high_scores:
            badge_w = int(self._w * 0.22)
            badge_h = int(self._h * 0.048)
            badge = pygame.Rect(cx - badge_w // 2, int(self._h * 0.355), badge_w, badge_h)
            ui.draw_panel(surf, badge, bg=(0, 0, 0, 160), border=c['hud_score'], bw=2)
            ui.px_text(surf, f"BEST  {high_scores[0]:07d}",
                       (cx, badge.centery), 26, c['hud_score'], center=True)

        ui.draw_button(surf, ui.btn_rect('play'),     "►  PLAY  ◄", 34)
        ui.draw_button(surf, ui.btn_rect('tutorial'), "TUTORIAL",   26)
        ui.draw_button(surf, ui.btn_rect('settings'), "SETTINGS",   26)
        ui.draw_button(surf, ui.btn_rect('exit'),     "EXIT",        26)

        ui.px_text(surf, "SPACE  or  click  PLAY  to  start",
                   (cx, int(self._h * 0.92)), 22, c['text_dim'], center=True)

    # ── Tutorial ─────────────────────────────────────────────────────────────

    def draw_tutorial(self, surf, scroll) -> int:
        """Draw the tutorial screen. Returns max_scroll."""
        cx = self._w // 2
        c  = ui.get_ui_colors()

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

        btn_h      = int(self._h * 0.10)
        btn_gap    = int(self._h * 0.015)
        title_h    = int(self._h * 0.13)
        panel_pad  = int(self._w  * 0.02)

        panel = pygame.Rect(panel_pad, int(self._h * 0.01),
                            self._w - panel_pad * 2, self._h - int(self._h * 0.02))
        ui.draw_panel(surf, panel, bg=c['panel_bg'], border=c['panel_border'], bw=5)

        title_y = panel.y + int(self._h * 0.04)
        ui.px_text(surf, "HOW  TO  PLAY", (cx, title_y), 90, c['title_sub'], center=True)

        div_y = panel.y + title_h
        pygame.draw.rect(surf, c['panel_border'], (panel.x + 20, div_y, panel.width - 40, 3))

        scroll_x = panel.x + int(self._w  * 0.03)
        scroll_y = div_y + 12
        scroll_w = panel.width - int(self._w  * 0.06)
        scroll_h = panel.bottom - scroll_y - btn_h - btn_gap - int(self._h * 0.02)

        lx_off = 0
        dx_off = int(self._w  * 0.24)

        content_h = sum(ROW_H if label else SEP_H for label, _ in rows) + ROW_H // 2
        max_scroll = max(0, content_h - scroll_h)

        content_surf = pygame.Surface((scroll_w, max(content_h, scroll_h)), pygame.SRCALPHA)
        ty = ROW_H // 4
        for label, desc in rows:
            if not label:
                ty += SEP_H
                pygame.draw.rect(content_surf, (*c['panel_border'][:3], 60),
                                 (0, ty - SEP_H // 2, scroll_w, 2))
                continue
            ui.px_text(content_surf, label, (lx_off, ty), ROW_FONT, c['text_highlight'])
            ui.px_text(content_surf, desc,  (dx_off, ty), ROW_FONT, c['text_main'])
            ty += ROW_H

        scroll_int = int(scroll)
        surf.set_clip(pygame.Rect(scroll_x, scroll_y, scroll_w, scroll_h))
        surf.blit(content_surf, (scroll_x, scroll_y),
                  pygame.Rect(0, scroll_int, scroll_w, scroll_h))
        surf.set_clip(None)

        if max_scroll > 0:
            sb_w      = 8
            sb_x      = scroll_x + scroll_w + 6
            sb_h      = scroll_h
            thumb_h   = max(40, int(sb_h * scroll_h / content_h))
            thumb_y   = scroll_y + int((sb_h - thumb_h) * scroll / max_scroll)
            pygame.draw.rect(surf, (*c['panel_border'][:3], 60),  (sb_x, scroll_y, sb_w, sb_h))
            pygame.draw.rect(surf, c['panel_border'],              (sb_x, thumb_y,  sb_w, thumb_h))

        back_bw   = int(self._w  * 0.22)
        back_bh   = int(self._h * 0.088)
        back_rect = pygame.Rect(cx - back_bw // 2,
                                panel.bottom - btn_h - btn_gap // 2,
                                back_bw, back_bh)
        ui.draw_button(surf, back_rect, "BACK", 54)
        ui.px_text(surf, "UP / DOWN to scroll    ESC or SPACE to go back",
                   (cx, panel.bottom - int(self._h * 0.008)), 22, c['text_dim'], center=True)

        return max_scroll

    # ── Settings ─────────────────────────────────────────────────────────────

    def draw_settings(self, surf, scroll, head_ctrl) -> int:
        """Draw the settings screen. Returns max_scroll."""
        cx = self._w // 2
        c  = ui.get_ui_colors()

        ROW_FONT = 55
        ROW_H    = 76
        SEP_H    = 38

        info_rows = [
            ("Move lane",  "Left / Right Arrow"),
            ("Jump",       "SPACE  —  double jump OK"),
            ("Coin boost", f"UP Arrow  —  costs {self._s.COIN_BOOST_COST} coins"),
            ("", ""),
            ("Boost dur.", f"{self._s.COIN_BOOST_DURATION:.0f}s  speed x2"),
            ("Key boost",  f"x{self._s.BOOST_MULTIPLIER} score  for  {self._s.BOOST_DURATION:.0f}s"),
            ("Day cycle",  "60s  per  day / night"),
            ("", ""),
            ("Shoot boss", "DOWN / S  —  fire coin at boss"),
            ("Restart",    "SPACE on Game Over screen"),
        ]

        panel_pad = int(self._w * 0.02)
        title_h   = int(self._h * 0.13)

        panel = pygame.Rect(panel_pad, int(self._h * 0.01),
                            self._w - panel_pad * 2, self._h - int(self._h * 0.02))
        ui.draw_panel(surf, panel, bg=c['panel_bg'], border=c['panel_border'], bw=5)

        title_y = panel.y + int(self._h * 0.04)
        ui.px_text(surf, "SETTINGS", (cx, title_y), 90, c['title_sub'], center=True)

        div_y = panel.y + title_h
        pygame.draw.rect(surf, c['panel_border'], (panel.x + 20, div_y, panel.width - 40, 3))

        scroll_x = panel.x + int(self._w * 0.03)
        scroll_y = div_y + 12
        scroll_w = panel.width - int(self._w * 0.06)
        scroll_h = ui.btn_rect('headctrl').top - int(self._h * 0.03) - scroll_y

        lx_off = 0
        dx_off = int(self._w * 0.22)

        content_h  = sum(ROW_H if label else SEP_H for label, _ in info_rows) + ROW_H // 4
        max_scroll = max(0, content_h - scroll_h)

        content_surf = pygame.Surface((scroll_w, max(content_h, scroll_h)), pygame.SRCALPHA)
        ty = ROW_H // 8
        for label, val in info_rows:
            if not label:
                ty += SEP_H
                pygame.draw.rect(content_surf, (*c['panel_border'][:3], 60),
                                 (0, ty - SEP_H // 2, scroll_w, 2))
                continue
            ui.px_text(content_surf, label + ":", (lx_off, ty), ROW_FONT, c['text_highlight'])
            ui.px_text(content_surf, val,          (dx_off, ty), ROW_FONT, c['text_main'])
            ty += ROW_H

        scroll_int = int(scroll)
        surf.set_clip(pygame.Rect(scroll_x, scroll_y, scroll_w, scroll_h))
        surf.blit(content_surf, (scroll_x, scroll_y),
                  pygame.Rect(0, scroll_int, scroll_w, scroll_h))
        surf.set_clip(None)

        if max_scroll > 0:
            sb_w    = 8
            sb_x    = scroll_x + scroll_w + 6
            sb_h    = scroll_h
            thumb_h = max(40, int(sb_h * scroll_h / content_h))
            thumb_y = scroll_y + int((sb_h - thumb_h) * scroll / max_scroll)
            pygame.draw.rect(surf, (*c['panel_border'][:3], 60), (sb_x, scroll_y, sb_w, sb_h))
            pygame.draw.rect(surf, c['panel_border'],             (sb_x, thumb_y,  sb_w, thumb_h))

        pygame.draw.rect(surf, c['panel_border'],
                         (panel.x + 20, ui.btn_rect('headctrl').top - int(self._h * 0.025),
                          panel.width - 40, 2))

        if head_ctrl.available:
            hc_label = "HEAD CONTROL:  ON " if head_ctrl.enabled else "HEAD CONTROL:  OFF"
            hc_desc  = ("Lean L/C/R = lane    Nod down = jump    Open mouth = shoot"
                        if head_ctrl.enabled else "Click to enable webcam head tracking")
            hc_col   = (80, 255, 160) if head_ctrl.enabled else c['text_dim']
        else:
            hc_label = "HEAD CONTROL:  N/A"
            hc_desc  = "pip install mediapipe opencv-python  to enable"
            hc_col   = c['title_404']
        ui.draw_button(surf, ui.btn_rect('headctrl'), hc_label, 30, hover=head_ctrl.enabled)
        ui.px_text(surf, hc_desc, (cx, ui.btn_rect('headctrl').bottom + 8), 22, hc_col, center=True)

        _CB_LABELS = ["COLORBLIND:  OFF", "COLORBLIND:  PROTANOPIA",
                      "COLORBLIND:  DEUTERANOPIA", "COLORBLIND:  TRITANOPIA", "COLORBLIND:  MONO"]
        _CB_DESCS  = ["Normal colours", "Red-blind: Blue/Yellow contrast",
                      "Green-blind: Blue/Yellow contrast", "Blue-blind: Red/Cyan contrast",
                      "White/Grey  +  shapes  +  numeric"]
        cb_col = c['text_highlight'] if self._s.colorblind_mode > 0 else c['text_dim']
        ui.draw_button(surf, ui.btn_rect('colorblind'), _CB_LABELS[self._s.colorblind_mode], 30,
                       hover=(self._s.colorblind_mode > 0))
        ui.px_text(surf, _CB_DESCS[self._s.colorblind_mode],
                   (cx, ui.btn_rect('colorblind').bottom + 8), 22, cb_col, center=True)

        ui.draw_button(surf, ui.btn_rect('back'), "BACK", 54)
        ui.px_text(surf, "UP / DOWN to scroll    ESC or SPACE to go back",
                   (cx, ui.btn_rect('back').bottom + int(self._h * 0.012)), 22, c['text_dim'],
                   center=True)

        return max_scroll

    # ── Game over ─────────────────────────────────────────────────────────────

    def draw_game_over(self, surf, score, collected_coins, high_scores):
        cx = self._w // 2
        c  = ui.get_ui_colors()

        overlay = pygame.Surface((self._w, self._h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 155))
        surf.blit(overlay, (0, 0))

        panel = pygame.Rect(cx - int(self._w * 0.23), int(self._h * 0.12),
                            int(self._w * 0.46), int(self._h * 0.76))
        ui.draw_panel(surf, panel, bg=c['panel_bg'], border=c['title_404'], bw=4)

        ui.px_text(surf, "GAME  OVER",
                   (cx, int(self._h * 0.195)), 62, c['title_404'],
                   shadow_col=c['title_404_shadow'], center=True)

        ui.px_text(surf, f"SCORE   {score:07d}",
                   (cx, int(self._h * 0.310)), 30, c['hud_score'], center=True)
        ui.px_text(surf, f"COINS   {collected_coins:02d}",
                   (cx, int(self._h * 0.375)), 24, c['title_sub'], center=True)

        ui.px_text(surf, "HIGH  SCORES",
                   (cx, int(self._h * 0.440)), 25, c['title_sub'], center=True)

        for i, s in enumerate(high_scores[:5]):
            col = c['hud_score'] if i == 0 else c['text_main']
            ui.px_text(surf, f"# {i+1}   {s:07d}",
                       (cx, int(self._h * 0.490) + i * int(self._h * 0.048)),
                       22, col, center=True)

        ui.draw_button(surf, ui.btn_rect('go_play'),     "PLAY AGAIN", 22)
        ui.draw_button(surf, ui.btn_rect('go_settings'), "SETTINGS",   22)
        ui.draw_button(surf, ui.btn_rect('go_menu'),     "MAIN MENU",  22)
        ui.draw_button(surf, ui.btn_rect('go_exit'),     "EXIT GAME",  22)
        ui.px_text(surf, "SPACE to restart",
                   (cx, int(self._h * 0.94)), 18, c['text_dim'], center=True)
