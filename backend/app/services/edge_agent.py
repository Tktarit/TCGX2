"""
EdgeAgent — measures cleanliness and straightness of all four card edges.

Each edge is scored 0–10:
  10 = sharp, perfectly straight edge
   0 = heavily worn, chipped, or frayed edge

Method per edge:
  1. Extract a thin border strip (EDGE_RATIO of the relevant dimension).
  2. Run Canny edge detection on the strip.
  3. Project edge pixels perpendicular to the edge direction → 1-D profile.
  4. Score = fraction of edge pixels that fall within ±PEAK_WINDOW rows/cols
     of the dominant peak, scaled to 0–10.

     A clean edge concentrates nearly all its Canny response in 1–2 pixels;
     a worn, frayed, or chipped edge scatters the response across many pixels.

Output:
  {
    "edge_scores": [top, bottom, left, right],  # each 0–10
    "score": float                               # average 0–10
  }
"""

import cv2
import numpy as np

EDGE_RATIO  = 0.07   # strip width = 7% of the corresponding image dimension
PEAK_WINDOW = 6      # pixels around the peak that count as "on the edge"
CANNY_T1    = 50
CANNY_T2    = 150


class EdgeAgent:
    def analyze(self, image: np.ndarray) -> dict:
        """
        Args:
            image: BGR card image (np.ndarray, uint8).
                   Should be already cropped to the card area.
        Returns:
            {"edge_scores": [top, bottom, left, right], "score": float}
        """
        gray  = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, CANNY_T1, CANNY_T2)

        h, w = edges.shape
        eh = max(1, int(h * EDGE_RATIO))
        ew = max(1, int(w * EDGE_RATIO))

        top    = self._h_score(edges[:eh,      :])
        bottom = self._h_score(edges[h - eh:,  :])
        left   = self._v_score(edges[:,   :ew     ])
        right  = self._v_score(edges[:,   w - ew: ])

        avg = round((top + bottom + left + right) / 4, 2)

        return {
            "edge_scores": [top, bottom, left, right],
            "score": avg,
        }

    @staticmethod
    def _h_score(strip: np.ndarray) -> float:
        """Score a horizontal edge strip (top or bottom)."""
        if strip.size == 0:
            return 0.0
        profile = np.sum(strip, axis=1).astype(float)   # row totals
        total = profile.sum()
        if total == 0:
            return 0.0
        peak = int(np.argmax(profile))
        lo = max(0, peak - PEAK_WINDOW)
        hi = min(strip.shape[0], peak + PEAK_WINDOW + 1)
        raw = min(1.0, profile[lo:hi].sum() / total)
        return round(8.0 + raw ** 0.5 * 2.0, 2)

    @staticmethod
    def _v_score(strip: np.ndarray) -> float:
        """Score a vertical edge strip (left or right)."""
        if strip.size == 0:
            return 0.0
        profile = np.sum(strip, axis=0).astype(float)   # column totals
        total = profile.sum()
        if total == 0:
            return 0.0
        peak = int(np.argmax(profile))
        lo = max(0, peak - PEAK_WINDOW)
        hi = min(strip.shape[1], peak + PEAK_WINDOW + 1)
        raw = min(1.0, profile[lo:hi].sum() / total)
        return round(8.0 + raw ** 0.5 * 2.0, 2)
