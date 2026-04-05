"""
Scoring logic: converts per-category image scores into a PSA grade estimate
and a submit recommendation.
"""

from dataclasses import dataclass
from app.services.image_processor import ImageAnalysis


@dataclass
class GradingResult:
    overall_score: float
    estimated_psa_grade: int
    recommend_submit: bool
    recommendation_reason: str


# PSA grading weights (must sum to 1.0)
WEIGHTS = {
    "corner": 0.35,
    "edge": 0.25,
    "surface": 0.25,
    "centering": 0.15,
}

# Minimum PSA grade to recommend submission (non-integer allows "between grades")
SUBMIT_GRADE_THRESHOLD = 9.5

# Minimum score thresholds per PSA grade
GRADE_THRESHOLDS = [
    (10, 92),
    (9,  82),
    (8,  72),
    (7,  62),
    (6,  52),
    (5,  42),
    (4,  32),
    (3,  22),
    (2,  12),
    (1,   0),
]


def compute_grade(analysis: ImageAnalysis) -> GradingResult:
    overall = (
        analysis.corner_score * WEIGHTS["corner"]
        + analysis.edge_score * WEIGHTS["edge"]
        + analysis.surface_score * WEIGHTS["surface"]
        + analysis.centering_score * WEIGHTS["centering"]
    )
    overall = round(overall, 2)

    grade = 1
    for g, threshold in GRADE_THRESHOLDS:
        if overall >= threshold:
            grade = g
            break

    recommend, reason = _recommendation(grade, overall, analysis)

    return GradingResult(
        overall_score=overall,
        estimated_psa_grade=grade,
        recommend_submit=recommend,
        recommendation_reason=reason,
    )


def _recommendation(
    grade: int, score: float, a: ImageAnalysis
) -> tuple[bool, str]:
    weaknesses = _find_weaknesses(a)

    if grade >= SUBMIT_GRADE_THRESHOLD:
        return (
            True,
            f"Estimated PSA {grade} — gem mint condition (score {score:.1f}/100). "
            f"High potential ROI from grading."
            + (f" Minor issues: {', '.join(weaknesses)}." if weaknesses else ""),
        )
    else:
        return (
            False,
            f"Estimated PSA {grade} — does not meet submission threshold "
            f"(score {score:.1f}/100, need PSA ≥ {SUBMIT_GRADE_THRESHOLD}). "
            "Grading cost likely exceeds added value. "
            f"Main issues: {', '.join(weaknesses) if weaknesses else 'general wear'}.",
        )


def _find_weaknesses(a: ImageAnalysis) -> list[str]:
    issues = []
    if a.corner_score < 70:
        issues.append(f"corner wear ({a.corner_score:.0f}/100)")
    if a.edge_score < 70:
        issues.append(f"edge damage ({a.edge_score:.0f}/100)")
    if a.surface_score < 70:
        issues.append(f"surface defects ({a.surface_score:.0f}/100)")
    if a.centering_score < 70:
        issues.append(f"off-center ({a.centering_score:.0f}/100)")
    return issues
