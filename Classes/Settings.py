import json
import os


_SAVE_FILE = "save_data.json"


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

        # ── Persistent data ───────────────────────────────────────────────────
        self.high_scores: list[int] = []

        self.load()

    # ── Persistence ───────────────────────────────────────────────────────────

    def save(self):
        """Write user preferences and high scores to disk."""
        data = {
            "colorblind_mode": self.colorblind_mode,
            "high_scores":     self.high_scores,
        }
        try:
            with open(_SAVE_FILE, "w") as f:
                json.dump(data, f)
        except OSError:
            pass

    def load(self):
        """Load user preferences and high scores from disk (silently on first run)."""
        if not os.path.exists(_SAVE_FILE):
            return
        try:
            with open(_SAVE_FILE) as f:
                data = json.load(f)
            self.colorblind_mode = int(data.get("colorblind_mode", 0)) % 5
            scores = data.get("high_scores", [])
            self.high_scores = sorted(
                [int(s) for s in scores if isinstance(s, (int, float))],
                reverse=True
            )[:5]
        except (OSError, ValueError, KeyError):
            pass

    # ── Actions ───────────────────────────────────────────────────────────────

    def cycle_colorblind(self):
        """Advance to the next colorblind mode and save."""
        self.colorblind_mode = (self.colorblind_mode + 1) % 5
        self.save()

    def add_score(self, score: int):
        """Insert a new score, keep top 5, and save."""
        self.high_scores.append(score)
        self.high_scores.sort(reverse=True)
        if len(self.high_scores) > 5:
            self.high_scores.pop()
        self.save()
