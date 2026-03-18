class Settings:
    def __init__(self):
        # ── Game balance ───────────────────────────────────────────────────────
        self.BASE_SPEED          = 0.1
        self.BOOST_DURATION      = 6.0
        self.BOOST_MULTIPLIER    = 3
        self.MAX_LIVES           = 3
        self.INVINCIBLE_DURATION = 2.0
        self.COIN_BOOST_COST     = 10
        self.COIN_BOOST_DURATION = 5.0
        self.BOSS_TRIGGER_TIME   = 60.0

        # ── User preferences ──────────────────────────────────────────────────
        # 0 = Off, 1 = Protanopia, 2 = Deuteranopia, 3 = Tritanopia, 4 = Monochrome
        self.colorblind_mode = 0
        self.PIXEL_FONT      = "fonts/PixelifySans.ttf"
