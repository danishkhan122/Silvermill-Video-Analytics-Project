"""
Weight machine number detection using EasyOCR.
Extracts numeric value from weight scale display, validates, and returns (annotated_frame, weight_float or None).
Used for truck weighbridge camera (cam 9).
"""
import re
import cv2
import numpy as np

_ocr_reader = None
_ocr_failed = False


def _init_ocr():
    """Lazy init EasyOCR for digits/numbers."""
    global _ocr_reader, _ocr_failed
    if _ocr_reader is not None:
        return True
    if _ocr_failed:
        return False
    try:
        import easyocr
        _ocr_reader = easyocr.Reader(["en"], gpu=bool(__import__("torch").cuda.is_available()), verbose=False)
        return True
    except Exception:
        _ocr_failed = True
        return False


def _extract_numeric_value(text):
    """
    Extract a single numeric value from text (digits and optional decimal).
    Returns float or None if invalid/empty.
    """
    if not text or not str(text).strip():
        return None
    # Allow digits, one decimal point, optional minus
    s = re.sub(r"[^\d.\-]", "", str(text).strip())
    # Take first contiguous number (e.g. "12.34 kg" -> 12.34)
    match = re.search(r"-?\d+\.?\d*", s)
    if not match:
        return None
    try:
        val = float(match.group())
        return val
    except ValueError:
        return None


def _validate_weight(value):
    """Ignore empty or invalid values. Reasonable range for kg (e.g. 0.1 to 999999)."""
    if value is None:
        return False
    try:
        v = float(value)
        if v < 0.1 or v > 999999.9:
            return False
        return True
    except (TypeError, ValueError):
        return False


def detect_weight(frame, conf_threshold=0.25):
    """
    Run OCR on weight machine frame; extract only numeric value and validate.
    Returns (annotated_frame, weight_float or None).
    """
    if frame is None or frame.size == 0:
        return frame, None
    if not _init_ocr():
        return frame, None
    out = frame.copy()
    h, w = frame.shape[:2]
    try:
        result = _ocr_reader.readtext(frame)
    except Exception:
        return out, None
    best_weight = None
    best_conf = 0.0
    for (bbox, text, conf) in (result or []):
        if conf < conf_threshold:
            continue
        val = _extract_numeric_value(text)
        if val is not None and _validate_weight(val) and conf > best_conf:
            best_weight = val
            best_conf = conf
    # Overlay detected weight on frame
    if best_weight is not None:
        label = f"Weight: {best_weight:.1f} kg"
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = min(1.2, max(0.6, w / 400))
        thickness = 2
        (tw, th), _ = cv2.getTextSize(label, font, font_scale, thickness)
        x = max(10, (w - tw) // 2 - 20)
        y = 50
        cv2.rectangle(out, (x - 5, y - th - 5), (x + tw + 5, y + 5), (0, 0, 0), -1)
        cv2.putText(out, label, (x, y), font, font_scale, (0, 255, 0), thickness, cv2.LINE_AA)
    return out, best_weight
