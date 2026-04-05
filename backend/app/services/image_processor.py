"""
OpenCV-based image analysis pipeline for trading cards.

Each method returns a score from 0–100:
  100 = perfect condition
    0 = severe damage
"""

import cv2
import numpy as np
from PIL import Image
from dataclasses import dataclass

from app.services.centering_agent import CenteringAgent


@dataclass
class ImageAnalysis:
    corner_score: float
    edge_score: float
    surface_score: float
    centering_score: float


def crop_card(image_path: str) -> np.ndarray:
    """
    Detect and crop the trading card from the image.

    Steps:
      1. Load image
      2. Grayscale + Gaussian blur to reduce noise
      3. Adaptive threshold → find contours
      4. Pick the largest contour (assumed to be the card)
      5. Return the cropped card region (BGR)

    Raises ValueError if the image cannot be read or no card is found.
    """
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise ValueError(f"Cannot read image: {image_path}")

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # Blur to suppress texture noise before edge detection
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)

    # Adaptive threshold handles varied lighting better than global Otsu
    thresh = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        blockSize=11, C=2,
    )

    # Close small gaps in the card border
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("No contours found — card not detected in image")

    largest = max(contours, key=cv2.contourArea)

    # Reject if the largest contour is suspiciously small (< 5% of image area)
    h, w = img_bgr.shape[:2]
    if cv2.contourArea(largest) < 0.05 * h * w:
        raise ValueError("Largest contour too small — card not detected in image")

    x, y, cw, ch = cv2.boundingRect(largest)
    cropped = img_bgr[y: y + ch, x: x + cw]

    return cropped


def normalize_image(image: np.ndarray) -> np.ndarray:
    """
    Apply CLAHE (Contrast Limited Adaptive Histogram Equalization) to each
    channel in LAB color space so brightness/contrast is leveled out without
    shifting hue — making analysis consistent regardless of shooting conditions.

    Args:
        image: BGR image (np.ndarray, uint8)
    Returns:
        Normalized BGR image (same shape/dtype)
    """
    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l_eq = clahe.apply(l)

    lab_eq = cv2.merge((l_eq, a, b))
    return cv2.cvtColor(lab_eq, cv2.COLOR_LAB2BGR)


def analyze_card(image_path: str) -> ImageAnalysis:
    img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        raise ValueError(f"Cannot read image: {image_path}")

    img_bgr = normalize_image(img_bgr)
    img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    return ImageAnalysis(
        corner_score=_analyze_corners(img_gray),
        edge_score=_analyze_edges(img_gray),
        surface_score=_analyze_surface(img_gray),
        centering_score=CenteringAgent().analyze(img_bgr) * 10.0,
    )


def _analyze_corners(gray: np.ndarray) -> float:
    """
    Detect corner wear using Harris corner detection.
    Worn corners have fewer sharp corner responses.
    """
    h, w = gray.shape
    corner_size = int(min(h, w) * 0.1)

    regions = [
        gray[:corner_size, :corner_size],          # top-left
        gray[:corner_size, w - corner_size:],       # top-right
        gray[h - corner_size:, :corner_size],       # bottom-left
        gray[h - corner_size:, w - corner_size:],   # bottom-right
    ]

    scores = []
    for region in regions:
        region_f = np.float32(region)
        harris = cv2.cornerHarris(region_f, blockSize=2, ksize=3, k=0.04)
        strong_corners = np.sum(harris > 0.01 * harris.max())
        # More sharp corner responses = better defined corner = higher score
        score = min(100.0, strong_corners * 5.0)
        scores.append(score)

    return float(np.mean(scores))


def _analyze_edges(gray: np.ndarray) -> float:
    """
    Measure edge straightness and uniformity.
    Frayed or chipped edges show up as irregular Canny edges.
    """
    edges = cv2.Canny(gray, threshold1=50, threshold2=150)

    h, w = gray.shape
    border = int(min(h, w) * 0.05)

    edge_strips = [
        edges[:border, :],           # top
        edges[h - border:, :],       # bottom
        edges[:, :border],           # left
        edges[:, w - border:],       # right
    ]

    scores = []
    for strip in edge_strips:
        if strip.size == 0:
            continue
        edge_density = np.sum(strip > 0) / strip.size
        # Ideal: clean line ~10–20% density. Noisy edges = damage.
        ideal_density = 0.15
        deviation = abs(edge_density - ideal_density)
        score = max(0.0, 100.0 - deviation * 300)
        scores.append(score)

    return float(np.mean(scores)) if scores else 50.0


def _analyze_surface(gray: np.ndarray) -> float:
    """
    Detect surface scratches and print defects using Laplacian variance.
    Low variance = smooth surface; very high local variance = scratches.
    """
    h, w = gray.shape
    border = int(min(h, w) * 0.1)
    surface = gray[border: h - border, border: w - border]

    laplacian = cv2.Laplacian(surface, cv2.CV_64F)
    local_var = cv2.blur(np.abs(laplacian).astype(np.float32), (15, 15))

    # High-variance patches = defects
    defect_threshold = float(np.mean(local_var)) + 2 * float(np.std(local_var))
    defect_ratio = np.sum(local_var > defect_threshold) / local_var.size

    score = max(0.0, 100.0 - defect_ratio * 500)
    return float(score)


