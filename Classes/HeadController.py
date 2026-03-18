"""
HeadController – real-time webcam head-pose input for accessibility.

Controls:
  Head in LEFT third   → lane 0 (left)
  Head in CENTER third → lane 1 (center)
  Head in RIGHT third  → lane 2 (right)
  Nod DOWN             → jump  (nod again while airborne = double jump)
  Open mouth wide      → shoot coin at boss

The screen is divided into 3 equal horizontal lanes.  Wherever the nose
centre sits determines the target lane directly — no threshold turning needed.

The background thread captures + processes every frame and stores an
annotated preview (numpy RGB) that the game renders as a live corner feed.

Requires:  pip install mediapipe opencv-python
"""

import threading
import time

# ── Tunable thresholds ────────────────────────────────────────────────────────
PITCH_THRESHOLD = 0.05   # normalised nose-y offset for down-nod
MOUTH_THRESHOLD = 0.028  # normalised lip-gap for shoot
DEBOUNCE_NOD    = 0.28   # s before next nod fires

# Lane zone boundaries (nose.x is 0=left … 1=right in the mirrored frame)
LANE_BOUNDARY_L = 1 / 3  # left-zone / center-zone divider
LANE_BOUNDARY_R = 2 / 3  # center-zone / right-zone divider
LANE_HYSTERESIS = 0.04   # dead-band around each boundary to prevent jitter


class HeadController:

    def __init__(self):
        self.available = False
        self.enabled   = False
        self.error_msg = ""

        # ── Events (written by thread, consumed by game frame) ────────────────
        self._lock           = threading.Lock()
        self._target_lane    = None   # 0 | 1 | 2, or None when no change
        self._pending_jumps  = 0
        self._pending_shoot  = False

        # Live annotated preview frame (numpy uint8 RGB, H×W×3)
        self._preview_frame  = None   # updated every processed webcam frame

        # ── Internal state ────────────────────────────────────────────────────
        self._current_zone  = 1      # last committed zone (0/1/2); start center
        self._in_pitch_down = False
        self._last_nod_time = 0.0
        self._in_mouth_open = False

        self._thread  = None
        self._running = False

        self._check_available()

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self):
        if not self.available:
            return False
        if self.enabled:
            return True
        self.error_msg  = ""
        self._running   = True
        self._thread    = threading.Thread(target=self._loop, daemon=True,
                                           name="HeadController")
        self._thread.start()
        self.enabled    = True
        return True

    def stop(self):
        self._running = False
        self.enabled  = False
        with self._lock:
            self._preview_frame = None

    def toggle(self):
        if self.enabled:
            self.stop()
        else:
            self.start()
        return self.enabled

    # ── Event consumers (call each game frame) ────────────────────────────────

    def consume_target_lane(self):
        """Return the target lane (0/1/2) if the zone changed, else None."""
        with self._lock:
            t = self._target_lane
            self._target_lane = None
            return t

    def consume_jump(self):
        with self._lock:
            if self._pending_jumps > 0:
                self._pending_jumps -= 1
                return True
            return False

    def consume_shoot(self):
        with self._lock:
            s = self._pending_shoot
            self._pending_shoot = False
            return s

    def get_preview_frame(self):
        """Return a copy of the latest annotated frame (numpy RGB) or None."""
        with self._lock:
            return None if self._preview_frame is None else self._preview_frame.copy()

    # ── Background thread ─────────────────────────────────────────────────────

    def _check_available(self):
        try:
            import cv2           # noqa: F401
            import mediapipe     # noqa: F401
            import numpy         # noqa: F401
            self.available = True
        except ImportError as exc:
            self.available = False
            self.error_msg = str(exc)

    def _loop(self):
        try:
            import cv2
            import mediapipe as mp
            from mediapipe.tasks.python import BaseOptions
            from mediapipe.tasks.python.vision import (
                FaceLandmarker, FaceLandmarkerOptions, RunningMode)
        except ImportError as exc:
            self.error_msg = str(exc)
            self.enabled   = False
            return

        import os
        model_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "face_landmarker.task")
        if not os.path.exists(model_path):
            self.error_msg = "face_landmarker.task not found"
            self.enabled   = False
            return

        try:
            options = FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=model_path),
                running_mode=RunningMode.IMAGE,
                num_faces=1,
                min_face_detection_confidence=0.4,
                min_tracking_confidence=0.4,
                min_face_presence_confidence=0.4,
                output_face_blendshapes=False,
                output_facial_transformation_matrixes=False,
            )
            face_landmarker = FaceLandmarker.create_from_options(options)
        except Exception as exc:
            self.error_msg = f"FaceLandmarker init failed: {exc}"
            self.enabled   = False
            return

        # Try camera indices 0, 1, 2 until one gives a real frame
        cap = None
        for cam_idx in range(3):
            c = cv2.VideoCapture(cam_idx)
            if c.isOpened():
                ok, test_frame = c.read()
                if ok and test_frame is not None:
                    cap = c
                    break
            c.release()
        if cap is None:
            self.error_msg = "Cannot open any webcam (tried 0-2)"
            self.enabled   = False
            face_landmarker.close()
            return

        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
        cap.set(cv2.CAP_PROP_AUTOFOCUS,    1)

        # Warm up: discard first 20 frames so auto-exposure stabilises
        for _ in range(20):
            cap.read()

        while self._running:
            ok, frame = cap.read()
            if not ok:
                time.sleep(0.01)
                continue

            # Mirror so turning head LEFT = left on screen
            frame = cv2.flip(frame, 1)
            rgb   = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            try:
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB,
                                    data=rgb.astype('uint8'))
                result   = face_landmarker.detect(mp_image)
            except Exception:
                continue

            lm        = result.face_landmarks[0] if result.face_landmarks else None
            nose_x    = 0.5
            pitch     = 0.0
            mouth_gap = 0.0

            if lm is not None:
                nose_x, pitch, mouth_gap = self._compute_pose(lm)
                self._update_events(nose_x, pitch, mouth_gap)

            annotated = self._annotate(frame, lm, nose_x, pitch, mouth_gap, cv2)
            rgb_ann   = cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB)

            with self._lock:
                self._preview_frame = rgb_ann

        cap.release()
        face_landmarker.close()

    # ── Pose computation ──────────────────────────────────────────────────────

    def _compute_pose(self, lm):
        nose      = lm[1]
        forehead  = lm[10]
        chin      = lm[152]
        upper_lip = lm[13]
        lower_lip = lm[14]

        face_h = abs(forehead.y - chin.y)
        if face_h < 1e-5:
            return 0.5, 0.0, 0.0

        fcy    = (forehead.y + chin.y) / 2
        nose_x = nose.x                            # 0=left … 1=right (mirrored)
        pitch  = (nose.y - fcy) / face_h           # + = head down
        mouth  = abs(upper_lip.y - lower_lip.y) / face_h
        return nose_x, pitch, mouth

    # ── Event generation ──────────────────────────────────────────────────────

    def _update_events(self, nose_x, pitch, mouth_gap):
        now = time.monotonic()
        with self._lock:
            # ── Lane zone (3-lane position mapping) ──────────────────────────
            z = self._current_zone
            if   z == 1 and nose_x < LANE_BOUNDARY_L - LANE_HYSTERESIS: z = 0
            elif z == 1 and nose_x > LANE_BOUNDARY_R + LANE_HYSTERESIS: z = 2
            elif z == 0 and nose_x > LANE_BOUNDARY_L + LANE_HYSTERESIS: z = 1
            elif z == 2 and nose_x < LANE_BOUNDARY_R - LANE_HYSTERESIS: z = 1
            if z != self._current_zone:
                self._current_zone = z
                self._target_lane  = z

            # Down-nod → jump
            if pitch > PITCH_THRESHOLD and not self._in_pitch_down:
                self._in_pitch_down = True
                if now - self._last_nod_time > DEBOUNCE_NOD:
                    self._pending_jumps += 1
                    self._last_nod_time  = now
            elif pitch < PITCH_THRESHOLD * 0.55:
                self._in_pitch_down = False

            # Mouth → shoot
            if mouth_gap > MOUTH_THRESHOLD and not self._in_mouth_open:
                self._pending_shoot = True
                self._in_mouth_open = True
            elif mouth_gap < MOUTH_THRESHOLD * 0.55:
                self._in_mouth_open = False

    # ── Frame annotation ──────────────────────────────────────────────────────

    def _annotate(self, frame, lm, nose_x, pitch, mouth_gap, cv2):
        h, w = frame.shape[:2]
        out  = frame.copy()

        # 3-lane zone dividers (always drawn)
        x_l = int(LANE_BOUNDARY_L * w)
        x_r = int(LANE_BOUNDARY_R * w)
        zone_cols = [(60, 60, 60), (60, 60, 60), (60, 60, 60)]
        if lm is not None:
            zone_cols[self._current_zone] = (0, 200, 80)
        for xi in (x_l, x_r):
            cv2.line(out, (xi, 0), (xi, h), (100, 100, 100), 1)
        lane_labels = ["L", "C", "R"]
        zone_xs = [x_l // 2, (x_l + x_r) // 2, (x_r + w) // 2]
        for i, (lx, col) in enumerate(zip(zone_xs, zone_cols)):
            cv2.putText(out, lane_labels[i], (lx - 6, 18),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, col, 2)

        if lm is not None:
            # Nose dot
            nx = int(nose_x * w)
            ny = int(lm[1].y * h)
            cv2.circle(out, (nx, ny), 7, (0, 0, 0),     -1)
            cv2.circle(out, (nx, ny), 5, (80, 255, 100), -1)

            # Pitch / nod indicator
            if pitch > PITCH_THRESHOLD:
                cv2.arrowedLine(out, (nx, 30), (nx, 55),
                                (0, 220, 255), 3, tipLength=0.4)
                cv2.putText(out, "NOD", (nx - 18, 28),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 220, 255), 1)

            # Mouth indicator (lips landmarks 13/14)
            mx = int((lm[13].x + lm[14].x) / 2 * w)
            my = int((lm[13].y + lm[14].y) / 2 * h)
            mouth_col = (0, 255, 150) if mouth_gap > MOUTH_THRESHOLD else (80, 80, 80)
            cv2.circle(out, (mx, my), 8, mouth_col, 2)
            if mouth_gap > MOUTH_THRESHOLD:
                cv2.putText(out, "SHOOT", (mx - 22, my - 12),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 150), 1)

        # Border — green when face found, red otherwise
        border = (0, 200, 80) if lm is not None else (0, 50, 200)
        cv2.rectangle(out, (0, 0), (w - 1, h - 1), border, 3)

        # Status strip at bottom
        cv2.rectangle(out, (0, h - 22), (w, h), (0, 0, 0), -1)
        status = "FACE DETECTED" if lm is not None else "NO FACE — point camera at your face"
        cv2.putText(out, status, (6, h - 6),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.42,
                    (80, 255, 80) if lm is not None else (80, 80, 255), 1)

        return out
