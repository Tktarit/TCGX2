"""
SurfaceAgent — detects surface defects on a trading card.

Two defect sources are combined:
  1. White spots  — bright anomalies on L channel (print defects, scratches
                    that expose white card stock)
  2. Scratch lines — linear features found by HoughLinesP on an edge map

Output:
  {
    "defect_count":    int,    # total discrete defects detected
    "defect_area_pct": float,  # % of card area covered by defect pixels
    "score":           float   # 0–10  (10 = pristine, 0 = severe damage)
  }

Scoring:
  score = 10 * exp(-k * defect_area_pct)
  k = 30  →  1 % area ≈ score 7.4,  5 % area ≈ score 2.2
"""

import cv2
import numpy as np

_SCORE_DECAY = 30.0          # exponential decay constant
_L_BRIGHT_THRESH = 240       # L* value above which a pixel is a "white spot"
_SCRATCH_THRESHOLD1 = 50     # Canny low threshold before Hough
_SCRATCH_THRESHOLD2 = 150    # Canny high threshold
_HOUGH_THRESHOLD = 30        # minimum votes for a line segment
_HOUGH_MIN_LENGTH = 20       # minimum line length in pixels
_HOUGH_MAX_GAP = 5           # maximum gap within a line segment
_SCRATCH_WIDTH = 2           # pixels to dilate each detected scratch line


class SurfaceAgent:
    def analyze(self, image: np.ndarray) -> dict:
        """
        Args:
            image: BGR card image (np.ndarray, uint8).
        Returns:
            {"defect_count": int, "defect_area_pct": float, "score": float}
        """
        h, w = image.shape[:2]
        total_pixels = h * w

        spot_mask    = self._detect_white_spots(image)
        scratch_mask = self._detect_scratches(image)

        combined = cv2.bitwise_or(spot_mask, scratch_mask)

        # Count connected components = discrete defect regions
        n_labels, _ = cv2.connectedComponents(combined)
        defect_count = max(0, n_labels - 1)   # label 0 is background

        defect_pixels   = int(np.count_nonzero(combined))
        defect_area_pct = round(defect_pixels / total_pixels * 100, 3)

        score = round(10.0 * float(np.exp(-_SCORE_DECAY * defect_area_pct / 100)), 2)

        return {
            "defect_count":    defect_count,
            "defect_area_pct": defect_area_pct,
            "score":           score,
        }

    # ── private helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _detect_white_spots(bgr: np.ndarray) -> np.ndarray:
        """
        Find anomalously bright pixels on the L channel of LAB.
        These correspond to print voids, surface chips, or light scratches
        that expose white card stock beneath the print layer.
        """
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        l_channel = lab[:, :, 0]

        # Values above threshold are suspiciously bright relative to surroundings
        _, bright_mask = cv2.threshold(
            l_channel, _L_BRIGHT_THRESH, 255, cv2.THRESH_BINARY
        )

        # Remove the natural outer border of the card (outermost 2% strip)
        # to avoid detecting the card's own white border as a defect
        h, w = bgr.shape[:2]
        bh, bw = max(1, int(h * 0.02)), max(1, int(w * 0.02))
        bright_mask[:bh,  :] = 0
        bright_mask[-bh:, :] = 0
        bright_mask[:, :bw ] = 0
        bright_mask[:, -bw:] = 0

        return bright_mask

    @staticmethod
    def _detect_scratches(bgr: np.ndarray) -> np.ndarray:
        """
        Detect linear scratch marks using Canny + HoughLinesP.
        Each detected line segment is drawn onto a mask with a small dilation
        to represent the physical width of the scratch.
        """
        gray  = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, _SCRATCH_THRESHOLD1, _SCRATCH_THRESHOLD2)

        scratch_mask = np.zeros_like(edges)

        lines = cv2.HoughLinesP(
            edges,
            rho=1,
            theta=np.pi / 180,
            threshold=_HOUGH_THRESHOLD,
            minLineLength=_HOUGH_MIN_LENGTH,
            maxLineGap=_HOUGH_MAX_GAP,
        )

        if lines is not None:
            for x1, y1, x2, y2 in lines[:, 0]:
                cv2.line(scratch_mask, (x1, y1), (x2, y2), 255, _SCRATCH_WIDTH)

        return scratch_mask
