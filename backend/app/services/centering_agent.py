"""
CenteringAgent — measures left/right and top/bottom border symmetry.

Score: 0–10
  10  = perfect 50/50 centering
  < 5 = ratio worse than 60/40 (PSA 8 threshold)
  0   = one border is zero (card flush against edge)

Formula per axis: score = 10 * (min_border / max_border) ** 2
  - ratio 1.0  → 10 * 1.0   = 10
  - ratio 0.67 → 10 * 0.449 = 4.49  (just below 5, matches 60/40 limit)
  - ratio 0.5  → 10 * 0.25  = 2.5
  Final score = average of LR score and TB score.
"""

import cv2
import numpy as np


class CenteringAgent:
    def analyze(self, bgr: np.ndarray) -> float:
        """
        Detect the card bounding box and score its centering.

        Args:
            bgr: BGR image (np.ndarray, uint8)
        Returns:
            float in [0.0, 10.0]
        """
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours:
            return 5.0  # no card detected — neutral fallback

        largest = max(contours, key=cv2.contourArea)
        x, y, cw, ch = cv2.boundingRect(largest)
        h, w = gray.shape

        left   = x
        right  = w - (x + cw)
        top    = y
        bottom = h - (y + ch)

        lr_score = self._axis_score(left, right)
        tb_score = self._axis_score(top, bottom)

        return round((lr_score + tb_score) / 2, 2)

    @staticmethod
    def _axis_score(a: int, b: int) -> float:
        """
        Score one axis (horizontal or vertical).

        ratio = min(a,b) / max(a,b)  →  always in (0, 1]
          ratio 1.0  → score 10   (50/50)
          ratio 0.67 → score 4.5  (60/40, < 5)
          ratio 0.0  → score 0    (card flush against edge)
        """
        if a + b == 0:
            return 10.0  # no border at all — treat as centered
        max_b = max(a, b)
        if max_b == 0:
            return 10.0
        ratio = min(a, b) / max_b
        return min(10.0, 10.0 * ratio ** 2)
