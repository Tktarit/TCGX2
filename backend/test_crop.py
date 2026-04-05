"""
Quick test for crop_card().
Usage:
    python test_crop.py <path_to_card_image>
    python test_crop.py  # uses a generated synthetic card if no arg given
"""

import sys
import cv2
import numpy as np
from app.services.image_processor import crop_card


def make_synthetic_card(path: str) -> None:
    """Draw a white rectangle (card) on a dark background and save it."""
    img = np.full((600, 500, 3), 40, dtype=np.uint8)   # dark background
    cv2.rectangle(img, (60, 80), (440, 520), (240, 240, 240), -1)  # card body
    cv2.rectangle(img, (60, 80), (440, 520), (80, 80, 80), 3)      # card border
    cv2.putText(img, "Pikachu", (150, 300), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 0, 0), 3)
    cv2.imwrite(path, img)
    print(f"Synthetic card saved → {path}")


def main():
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
    else:
        image_path = "test_card_input.png"
        make_synthetic_card(image_path)

    print(f"Input : {image_path}")

    cropped = crop_card(image_path)

    out_path = "test_card_cropped.png"
    cv2.imwrite(out_path, cropped)

    h, w = cropped.shape[:2]
    orig = cv2.imread(image_path)
    oh, ow = orig.shape[:2]

    print(f"Original size : {ow} x {oh}")
    print(f"Cropped size  : {w} x {h}")
    print(f"Output saved  → {out_path}")
    print("crop_card() OK")


if __name__ == "__main__":
    main()
