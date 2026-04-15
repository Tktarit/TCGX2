import cv2
import numpy as np


def _imread(path: str) -> np.ndarray | None:
    """อ่านภาพรองรับทุก format รวมถึง AVIF, HEIC และ Windows path."""
    # ลอง OpenCV ก่อน (เร็วกว่า, รองรับ jpg/png/webp)
    buf = np.fromfile(path, dtype=np.uint8)
    if buf.size == 0:
        return None
    img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
    if img is not None:
        return img
    # Fallback: PIL รองรับ AVIF และ format อื่นที่ OpenCV ไม่รองรับ
    try:
        from PIL import Image
        pil = Image.open(path).convert("RGB")
        return cv2.cvtColor(np.array(pil), cv2.COLOR_RGB2BGR)
    except Exception:
        return None


def _has_card_edges(img_bgr: np.ndarray) -> bool:
    """
    ตรวจว่าภาพมีโครงสร้างสี่เหลี่ยมของการ์ด
    โดยหาเส้นตรงยาว >= 2 เส้นแนวนอน + >= 2 เส้นแนวตั้ง
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 50, 150)
    h, w = edges.shape
    min_len = min(h, w) * 0.25  # เส้นต้องยาวอย่างน้อย 25% ของด้านสั้น

    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180,
        threshold=60, minLineLength=min_len, maxLineGap=30,
    )
    if lines is None:
        return False

    h_count = v_count = 0
    for x1, y1, x2, y2 in lines[:, 0]:
        angle = abs(np.degrees(np.arctan2(y2 - y1, x2 - x1)))
        if angle < 25 or angle > 155:
            h_count += 1
        elif 65 < angle < 115:
            v_count += 1

    return h_count >= 2 and v_count >= 2


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
    img_bgr = _imread(image_path)
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

    # Close gaps in the card border — รองรับนิ้วที่ถือการ์ด
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
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

    # ตรวจโครงสร้างเส้นตรงของการ์ด — ต้องมีเส้นยาวแนวนอน + แนวตั้ง
    if not _has_card_edges(img_bgr):
        raise ValueError("ไม่ใช่การ์ด — ไม่พบขอบสี่เหลี่ยมในภาพ")

    # ใช้ minAreaRect เพื่อรองรับการ์ดที่เอียง — กรอบหมุนตามการ์ดได้
    _, (rw, rh), _ = cv2.minAreaRect(largest)
    if rw < 1 or rh < 1:
        raise ValueError("ไม่ใช่การ์ด — ตรวจจับขอบไม่ได้")

    # Check aspect ratio — trading cards are roughly 1.2:1 to 1.9:1 (portrait or landscape)
    aspect = max(rw, rh) / min(rw, rh)
    if aspect < 1.1 or aspect > 2.5:
        raise ValueError(f"ไม่ใช่การ์ด — สัดส่วนภาพ ({aspect:.2f}) ไม่ตรงกับรูปแบบการ์ดสะสม")

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



