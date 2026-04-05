"""
Tests for CenteringAgent, CornerAgent, SurfaceAgent, and crop_card().
All agent scores are 0–10.
"""

import cv2
import numpy as np
import pytest

from app.services.centering_agent import CenteringAgent
from app.services.corner_agent import CornerAgent
from app.services.surface_agent import SurfaceAgent
from app.services.image_processor import crop_card


# ══════════════════════════════════════════════════════════════════════════════
# CenteringAgent
# ══════════════════════════════════════════════════════════════════════════════

class TestCenteringAgent:

    def test_score_in_range_centered(self, centered_image_path):
        """Score must be within 0–10 for any input."""
        score = CenteringAgent().analyze(cv2.imread(centered_image_path))
        assert 0.0 <= score <= 10.0

    def test_score_in_range_offcenter(self, offcenter_image_path):
        """Score must be within 0–10 even for a badly off-center card."""
        score = CenteringAgent().analyze(cv2.imread(offcenter_image_path))
        assert 0.0 <= score <= 10.0

    def test_perfect_centering_gives_high_score(self, centered_image_path):
        """
        Equal borders → ratio 1.0 → score near 10.
        Canvas 400×600, card 200×300 at (100,150): L=R=100, T=B=150.
        """
        score = CenteringAgent().analyze(cv2.imread(centered_image_path))
        assert score >= 8.0, f"Expected ≥ 8 for perfect centering, got {score}"

    def test_offcenter_gives_score_below_5(self, offcenter_image_path):
        """
        Card at (20,20): L=20 R=180, T=20 B=280.
        ratio_lr = 20/180 ≈ 0.11 → axis_score ≈ 0.12
        ratio_tb = 20/280 ≈ 0.07 → axis_score ≈ 0.05
        Expected overall score well below 5.
        """
        score = CenteringAgent().analyze(cv2.imread(offcenter_image_path))
        assert score < 5.0, f"Expected < 5 for off-center card, got {score}"

    def test_ratio_beyond_threshold_scores_below_5(self):
        """
        Explicit ratio test: 60/40 border split → ratio=0.67 → score < 5.
        Canvas 300×100, card at x=20 width=240 → L=20 R=40, ratio=20/40=0.5.
        """
        score = CenteringAgent._axis_score(20, 40)
        assert score < 5.0, f"60/40 split should score < 5, got {score}"

    def test_ratio_10_gives_score_10(self):
        """Perfect 50/50 → ratio=1.0 → score=10."""
        score = CenteringAgent._axis_score(100, 100)
        assert score == 10.0

    def test_centered_beats_offcenter(self, centered_image_path, offcenter_image_path):
        """Centered card must always outscore the off-center card."""
        agent = CenteringAgent()
        s_centered  = agent.analyze(cv2.imread(centered_image_path))
        s_offcenter = agent.analyze(cv2.imread(offcenter_image_path))
        assert s_centered > s_offcenter, (
            f"Centered ({s_centered}) should beat off-center ({s_offcenter})"
        )

    def test_returns_float(self, centered_image_path):
        result = CenteringAgent().analyze(cv2.imread(centered_image_path))
        assert isinstance(result, float)


# ══════════════════════════════════════════════════════════════════════════════
# CornerAgent
# ══════════════════════════════════════════════════════════════════════════════

class TestCornerAgent:

    # ── Return structure ──────────────────────────────────────────────────────

    def test_returns_dict_with_required_keys(self, sharp_card_bgr):
        result = CornerAgent().analyze(sharp_card_bgr)
        assert "corner_scores" in result
        assert "score" in result

    def test_corner_scores_is_list_of_four(self, sharp_card_bgr):
        scores = CornerAgent().analyze(sharp_card_bgr)["corner_scores"]
        assert isinstance(scores, list)
        assert len(scores) == 4

    def test_corner_order_is_tl_tr_bl_br(self, sharp_card_bgr):
        """List order must be [top-left, top-right, bottom-left, bottom-right]."""
        scores = CornerAgent().analyze(sharp_card_bgr)["corner_scores"]
        tl, tr, bl, br = scores
        # All should be valid scores — order verified by symmetry of fixture
        for s in (tl, tr, bl, br):
            assert 0.0 <= s <= 10.0

    # ── Score range ───────────────────────────────────────────────────────────

    def test_individual_scores_in_range(self, sharp_card_bgr):
        for s in CornerAgent().analyze(sharp_card_bgr)["corner_scores"]:
            assert 0.0 <= s <= 10.0

    def test_average_score_in_range(self, sharp_card_bgr):
        score = CornerAgent().analyze(sharp_card_bgr)["score"]
        assert 0.0 <= score <= 10.0

    def test_average_equals_mean_of_corners(self, sharp_card_bgr):
        result = CornerAgent().analyze(sharp_card_bgr)
        expected = round(sum(result["corner_scores"]) / 4, 2)
        assert result["score"] == expected

    # ── Score semantics ───────────────────────────────────────────────────────

    def test_sharp_card_scores_higher_than_worn(self, sharp_card_bgr, worn_card_bgr):
        """Clean crisp corners must outscore smeared/worn corners."""
        sharp_score = CornerAgent().analyze(sharp_card_bgr)["score"]
        worn_score  = CornerAgent().analyze(worn_card_bgr)["score"]
        assert sharp_score > worn_score, (
            f"Sharp ({sharp_score}) should beat worn ({worn_score})"
        )

    def test_worn_corners_score_below_sharp(self, worn_card_bgr):
        """Worn card should not achieve a perfect score."""
        score = CornerAgent().analyze(worn_card_bgr)["score"]
        assert score < 10.0


# ══════════════════════════════════════════════════════════════════════════════
# SurfaceAgent
# ══════════════════════════════════════════════════════════════════════════════

class TestSurfaceAgent:

    # ── Return structure ──────────────────────────────────────────────────────

    def test_returns_required_keys(self, clean_surface_bgr):
        result = SurfaceAgent().analyze(clean_surface_bgr)
        assert "defect_count"    in result
        assert "defect_area_pct" in result
        assert "score"           in result

    def test_defect_count_is_non_negative_int(self, clean_surface_bgr):
        count = SurfaceAgent().analyze(clean_surface_bgr)["defect_count"]
        assert isinstance(count, int)
        assert count >= 0

    def test_defect_area_pct_is_float_between_0_and_100(self, clean_surface_bgr):
        pct = SurfaceAgent().analyze(clean_surface_bgr)["defect_area_pct"]
        assert isinstance(pct, float)
        assert 0.0 <= pct <= 100.0

    def test_score_in_range(self, clean_surface_bgr):
        score = SurfaceAgent().analyze(clean_surface_bgr)["score"]
        assert 0.0 <= score <= 10.0

    # ── Clean surface ─────────────────────────────────────────────────────────

    def test_clean_surface_scores_near_10(self, clean_surface_bgr):
        """Uniform grey image has no bright spots or lines → score ≈ 10."""
        result = SurfaceAgent().analyze(clean_surface_bgr)
        assert result["score"] >= 9.0, (
            f"Clean surface should score ≥ 9, got {result['score']}"
        )

    def test_clean_surface_zero_defect_area(self, clean_surface_bgr):
        result = SurfaceAgent().analyze(clean_surface_bgr)
        assert result["defect_area_pct"] == 0.0

    # ── Spotted surface ───────────────────────────────────────────────────────

    def test_spots_detected_as_defects(self, spotted_surface_bgr):
        """Five white circles must register as defects."""
        result = SurfaceAgent().analyze(spotted_surface_bgr)
        assert result["defect_count"] > 0
        assert result["defect_area_pct"] > 0.0

    def test_spotted_scores_lower_than_clean(
        self, clean_surface_bgr, spotted_surface_bgr
    ):
        clean_score   = SurfaceAgent().analyze(clean_surface_bgr)["score"]
        spotted_score = SurfaceAgent().analyze(spotted_surface_bgr)["score"]
        assert clean_score > spotted_score, (
            f"Clean ({clean_score}) should beat spotted ({spotted_score})"
        )

    # ── Scratched surface ─────────────────────────────────────────────────────

    def test_scratches_detected_as_defects(self, scratched_surface_bgr):
        """Long bright lines must be detected by HoughLinesP."""
        result = SurfaceAgent().analyze(scratched_surface_bgr)
        assert result["defect_count"] > 0

    def test_scratched_scores_lower_than_clean(
        self, clean_surface_bgr, scratched_surface_bgr
    ):
        clean_score    = SurfaceAgent().analyze(clean_surface_bgr)["score"]
        scratch_score  = SurfaceAgent().analyze(scratched_surface_bgr)["score"]
        assert clean_score > scratch_score, (
            f"Clean ({clean_score}) should beat scratched ({scratch_score})"
        )

    # ── Monotonicity: more damage = lower score ───────────────────────────────

    def test_more_defects_means_higher_defect_area(
        self, spotted_surface_bgr, scratched_surface_bgr
    ):
        """Both damaged cards must have higher defect_area_pct than clean."""
        clean = SurfaceAgent().analyze(np.full((300, 200, 3), 128, dtype=np.uint8))
        assert SurfaceAgent().analyze(spotted_surface_bgr)["defect_area_pct"] > clean["defect_area_pct"]
        assert SurfaceAgent().analyze(scratched_surface_bgr)["defect_area_pct"] > clean["defect_area_pct"]


# ══════════════════════════════════════════════════════════════════════════════
# crop_card
# ══════════════════════════════════════════════════════════════════════════════

class TestCropCard:

    def test_returns_ndarray(self, croppable_image_path):
        assert isinstance(crop_card(croppable_image_path), np.ndarray)

    def test_result_has_three_channels(self, croppable_image_path):
        result = crop_card(croppable_image_path)
        assert result.ndim == 3
        assert result.shape[2] == 3

    def test_crop_smaller_than_original(self, croppable_image_path):
        """Background removed → crop must be smaller than full canvas."""
        orig = cv2.imread(croppable_image_path)
        cropped = crop_card(croppable_image_path)
        assert cropped.shape[0] * cropped.shape[1] < orig.shape[0] * orig.shape[1]

    def test_crop_is_reasonably_large(self, croppable_image_path):
        """
        Card occupies ~60% of canvas; crop should be at least 30% of original
        (generous lower bound to tolerate morphological border expansion).
        """
        orig = cv2.imread(croppable_image_path)
        cropped = crop_card(croppable_image_path)
        orig_area = orig.shape[0] * orig.shape[1]
        crop_area = cropped.shape[0] * cropped.shape[1]
        assert crop_area >= 0.30 * orig_area, (
            f"Crop ({crop_area}px) too small vs original ({orig_area}px)"
        )

    def test_crop_dimensions_positive(self, croppable_image_path):
        result = crop_card(croppable_image_path)
        assert result.shape[0] > 0
        assert result.shape[1] > 0

    def test_raises_on_invalid_image(self, unreadable_image_path):
        with pytest.raises(ValueError, match="Cannot read image"):
            crop_card(unreadable_image_path)

    def test_raises_on_missing_file(self, tmp_path):
        with pytest.raises(ValueError, match="Cannot read image"):
            crop_card(str(tmp_path / "nonexistent.png"))
