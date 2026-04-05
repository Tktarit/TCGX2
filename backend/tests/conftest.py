"""
Shared fixtures: synthetic card images with known geometry.
All images are white card on dark background so thresholding is predictable.
"""

import cv2
import numpy as np
import pytest
import tempfile
import os


def _save_temp(img: np.ndarray, suffix: str = ".png") -> str:
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    cv2.imwrite(path, img)
    return path


def _make_card_image(
    canvas_w: int,
    canvas_h: int,
    card_x: int,
    card_y: int,
    card_w: int,
    card_h: int,
) -> np.ndarray:
    """Dark background + white card rectangle."""
    img = np.full((canvas_h, canvas_w, 3), 30, dtype=np.uint8)
    cv2.rectangle(
        img,
        (card_x, card_y),
        (card_x + card_w, card_y + card_h),
        (240, 240, 240),
        -1,
    )
    return img


# ── Centering fixtures ──────────────────────────────────────────────────────

@pytest.fixture()
def centered_image_path():
    """Card perfectly centered: equal borders on all four sides."""
    # Canvas 400×600, card 200×300 → borders: L=100 R=100 T=150 B=150
    img = _make_card_image(400, 600, card_x=100, card_y=150, card_w=200, card_h=300)
    path = _save_temp(img)
    yield path
    os.unlink(path)


@pytest.fixture()
def offcenter_image_path():
    """Card pushed to top-left: L=20 R=180, T=20 B=280 → heavily off-center."""
    img = _make_card_image(400, 600, card_x=20, card_y=20, card_w=200, card_h=300)
    path = _save_temp(img)
    yield path
    os.unlink(path)


# ── Crop fixtures ────────────────────────────────────────────────────────────

@pytest.fixture()
def croppable_image_path():
    """Card occupies ~60% of canvas — should crop down to near card size."""
    # Canvas 500×700, card 300×450 centred
    img = _make_card_image(500, 700, card_x=100, card_y=125, card_w=300, card_h=450)
    path = _save_temp(img)
    yield path
    os.unlink(path)


# ── Corner fixtures ──────────────────────────────────────────────────────────

def _make_sharp_card(h: int = 300, w: int = 200) -> np.ndarray:
    """Dark background + white card with crisp rectangular corners."""
    img = np.full((h, w, 3), 30, dtype=np.uint8)
    margin = int(min(h, w) * 0.08)
    cv2.rectangle(
        img,
        (margin, margin),
        (w - margin, h - margin),
        (240, 240, 240),
        -1,
    )
    return img


@pytest.fixture()
def sharp_card_bgr():
    """Card with sharp 90-degree corners (white rect on dark background)."""
    return _make_sharp_card()


@pytest.fixture()
def worn_card_bgr():
    """
    Same card but corner patches (exactly the regions CornerAgent crops)
    are filled with background colour — simulates chipped/missing material.
    Guarantees zero edge density in all four corner patches → score < sharp.
    """
    img = _make_sharp_card()
    h, w = img.shape[:2]
    ch = max(1, int(h * 0.10))   # matches CornerAgent.CORNER_RATIO
    cw = max(1, int(w * 0.10))
    bg = (30, 30, 30)             # same as background in _make_sharp_card

    for (y0, y1, x0, x1) in [
        (0,      ch, 0,      cw),   # top-left
        (0,      ch, w - cw, w ),   # top-right
        (h - ch, h,  0,      cw),   # bottom-left
        (h - ch, h,  w - cw, w ),   # bottom-right
    ]:
        img[y0:y1, x0:x1] = bg
    return img


# ── Surface fixtures ─────────────────────────────────────────────────────────

@pytest.fixture()
def clean_surface_bgr():
    """Uniform mid-grey card — no bright spots, no linear scratches."""
    return np.full((300, 200, 3), 128, dtype=np.uint8)


@pytest.fixture()
def spotted_surface_bgr():
    """Card with several bright white spots simulating print defects."""
    img = np.full((300, 200, 3), 128, dtype=np.uint8)
    for (cx, cy) in [(40, 60), (100, 150), (160, 80), (80, 220), (140, 260)]:
        cv2.circle(img, (cx, cy), 8, (255, 255, 255), -1)
    return img


@pytest.fixture()
def scratched_surface_bgr():
    """Card with several long bright scratch lines."""
    img = np.full((300, 200, 3), 128, dtype=np.uint8)
    for (x1, y1, x2, y2) in [
        (10,  50,  190,  60),
        (20, 120,  180, 130),
        (30, 200,  170, 210),
    ]:
        cv2.line(img, (x1, y1), (x2, y2), (255, 255, 255), 2)
    return img


@pytest.fixture()
def unreadable_image_path(tmp_path):
    """File that exists but is not a valid image."""
    p = tmp_path / "bad.png"
    p.write_bytes(b"not an image")
    return str(p)
