"""
CornerAgent — measures sharpness of all four card corners.

Each corner is scored 0–10:
  10 = crisp, well-defined corner (high edge density in a tight region)
   0 = completely worn/missing corner (no edges detected)

A worn corner loses its sharp 90-degree edge response:
  - Mint corner   → dense, localised Canny edges along two border lines
  - Worn corner   → edges spread out, density in the corner patch drops

Score formula per corner:
  edge_density = edge_pixels / total_pixels  (in the corner patch)
  score = clamp(edge_density / TARGET_DENSITY, 0, 1) * 10
  TARGET_DENSITY = 0.20  (empirically good for a clean card corner)

Final output:
  {
    "corner_scores": [tl, tr, bl, br],   # each 0–10
    "score": float                        # average 0–10
  }
"""

import cv2
import numpy as np


TARGET_DENSITY = 0.20   # edge pixel ratio expected for a crisp corner
CORNER_RATIO   = 0.10   # crop size = 10% of card dimension per side


class CornerAgent:
    def analyze(self, image: np.ndarray) -> dict:
        """
        Args:
            image: BGR card image (np.ndarray, uint8).
                   Should be already cropped to the card area.
        Returns:
            {"corner_scores": [tl, tr, bl, br], "score": float}
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, threshold1=50, threshold2=150)

        h, w = edges.shape
        ch = max(1, int(h * CORNER_RATIO))
        cw = max(1, int(w * CORNER_RATIO))

        patches = {
            "tl": edges[:ch,      :cw     ],
            "tr": edges[:ch,      w - cw: ],
            "bl": edges[h - ch:,  :cw     ],
            "br": edges[h - ch:,  w - cw: ],
        }

        tl = self._patch_score(patches["tl"])
        tr = self._patch_score(patches["tr"])
        bl = self._patch_score(patches["bl"])
        br = self._patch_score(patches["br"])

        avg = round((tl + tr + bl + br) / 4, 2)

        return {
            "corner_scores": [tl, tr, bl, br],
            "score": avg,
        }

    @staticmethod
    def _patch_score(patch: np.ndarray) -> float:
        """
        Score a single corner patch by its Canny edge density.

        A pristine corner has two clean lines meeting at ~90°, giving a
        predictable edge density.  Fuzz, rounding, or missing material
        either removes those lines (density drops) or smears them
        (edges scatter, density per line drops while noise rises — net
        effect is still a lower clean-line density).
        """
        if patch.size == 0:
            return 0.0
        density = np.count_nonzero(patch) / patch.size
        score = min(1.0, density / TARGET_DENSITY) * 10.0
        return round(score, 2)
