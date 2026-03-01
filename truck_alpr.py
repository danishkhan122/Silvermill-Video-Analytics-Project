"""
ALPR (Automatic License Plate Recognition) using train_models/alpr.pt and EasyOCR.
Detects number plates, crops region, runs OCR for clean text. Used for truck front/back cameras.
"""
import os
import cv2
import numpy as np

_alpr_model = None
_ocr_reader = None
_alpr_model_path = None
_ocr_ready = False

# Camera IDs for license plates (front=6, back=7)
PLATE_CAM_IDS = (6, 7)


def _get_alpr_path():
    global _alpr_model_path
    if _alpr_model_path is not None:
        return _alpr_model_path
    root = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(root, "train_models", "alpr.pt")
    _alpr_model_path = path
    return path


def load_alpr_model():
    """Load YOLO ALPR model (train_models/alpr.pt). Returns True if loaded."""
    global _alpr_model
    if _alpr_model is not None:
        return True
    path = _get_alpr_path()
    if not os.path.isfile(path):
        return False
    try:
        from ultralytics import YOLO
        _alpr_model = YOLO(path)
        # Warmup
        dummy = np.zeros((320, 320, 3), dtype=np.uint8)
        _alpr_model.predict(dummy, conf=0.25, verbose=False)
        return True
    except Exception:
        return False


def _init_easyocr():
    """Lazy init EasyOCR (reader for English + digits)."""
    global _ocr_reader, _ocr_ready
    if _ocr_reader is not None:
        return True
    if getattr(_init_easyocr, "_failed", False):
        return False
    try:
        import easyocr
        _ocr_reader = easyocr.Reader(["en"], gpu=bool(__import__("torch").cuda.is_available()), verbose=False)
        _ocr_ready = True
        return True
    except Exception:
        _init_easyocr._failed = True
        return False


def run_ocr_on_crop(crop_bgr):
    """Run EasyOCR on a cropped plate image. Returns cleaned plate text or empty string."""
    if crop_bgr is None or crop_bgr.size == 0:
        return ""
    if not _init_easyocr():
        return ""
    try:
        # EasyOCR expects RGB for some versions; we pass BGR, often works
        result = _ocr_reader.readtext(crop_bgr)
        if not result:
            return ""
        # Prefer result with largest bbox area or first
        texts = []
        for (bbox, text, conf) in result:
            if text and conf > 0.2:
                t = str(text).strip().upper()
                # Keep alphanumeric and common plate chars
                t = "".join(c for c in t if c.isalnum() or c in "- ")
                if t:
                    texts.append(t)
        return " ".join(texts).strip() if texts else ""
    except Exception:
        return ""


def detect_plates(frame, conf_threshold=0.35):
    """
    Run ALPR model on frame. Returns list of (x1,y1,x2,y2, crop_bgr).
    Crop is the plate region for OCR.
    """
    if frame is None or frame.size == 0:
        return []
    if not load_alpr_model():
        return []
    try:
        results = _alpr_model.predict(
            frame,
            conf=conf_threshold,
            verbose=False,
            imgsz=640,
        )
    except Exception:
        return []
    out = []
    h, w = frame.shape[:2]
    for result in results:
        if result.boxes is None:
            continue
        boxes = result.boxes
        for i in range(len(boxes)):
            x1, y1, x2, y2 = boxes.xyxy[i].cpu().numpy()
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            x1 = max(0, min(x1, w - 1))
            x2 = max(0, min(x2, w))
            y1 = max(0, min(y1, h - 1))
            y2 = max(0, min(y2, h))
            if x2 <= x1 or y2 <= y1:
                continue
            crop = frame[y1:y2, x1:x2]
            if crop.size == 0:
                continue
            out.append((x1, y1, x2, y2, crop))
    return out


def detect_and_ocr(frame, conf_threshold=0.30):
    """
    Detect number plates with train_models/alpr.pt; draw a clear bounding box on every plate.
    Run OCR on best (largest) crop. Returns (annotated_frame, plate_text, plate_crop or None).
    """
    if frame is None or frame.size == 0:
        return frame, "", None
    out_frame = frame.copy()
    dets = detect_plates(frame, conf_threshold=conf_threshold)
    plate_text = ""
    best_crop = None
    best_area = 0
    best_box = None
    h, w = frame.shape[:2]
    for (x1, y1, x2, y2, crop) in dets:
        area = (x2 - x1) * (y2 - y1)
        if area > best_area and crop.size > 0:
            best_area = area
            best_crop = crop
            best_box = (x1, y1, x2, y2)
    if best_crop is not None:
        plate_text = run_ocr_on_crop(best_crop)
        if best_box:
            x1, y1, x2, y2 = best_box
            # Thick green bounding box on main number plate
            color = (0, 255, 0)  # BGR green
            thickness = 3
            cv2.rectangle(out_frame, (x1, y1), (x2, y2), color, thickness)
            cv2.rectangle(out_frame, (x1, y1), (x2, y2), (255, 255, 255), 1)  # thin white outline
            label = plate_text if plate_text else "Number Plate"
            cv2.putText(
                out_frame, label, (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.75, (0, 255, 0), 2, cv2.LINE_AA
            )
            if plate_text:
                cv2.putText(
                    out_frame, plate_text, (x1, y2 + 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA
                )
            # Always use padded crop for sidebar (so right panel shows plate as soon as detected)
            pad = max(4, int(0.05 * min(x2 - x1, y2 - y1)))
            x1p = max(0, x1 - pad)
            y1p = max(0, y1 - pad)
            x2p = min(w, x2 + pad)
            y2p = min(h, y2 + pad)
            if x2p > x1p and y2p > y1p:
                best_crop = frame[y1p:y2p, x1p:x2p].copy()
    # Draw bounding box on every other detected plate
    for (x1, y1, x2, y2, crop) in dets:
        if best_box and (x1, y1, x2, y2) == best_box:
            continue
        color = (255, 200, 0)  # BGR cyan/orange
        thickness = 2
        cv2.rectangle(out_frame, (x1, y1), (x2, y2), color, thickness)
        cv2.putText(
            out_frame, "Number Plate", (x1, y1 - 6),
            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2, cv2.LINE_AA
        )
    # Return plate crop whenever we have a detection (so right panel shows it even if OCR empty)
    return out_frame, plate_text.strip(), best_crop


# ---------- OpenCV frontal face detection (driver camera: face on front side) ----------
_face_cascade = None


def _get_face_cascade():
    """Lazy-load OpenCV frontal face cascade for front-facing face detection."""
    global _face_cascade
    if _face_cascade is not None:
        return _face_cascade
    path = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
    if os.path.isfile(path):
        _face_cascade = cv2.CascadeClassifier(path)
    return _face_cascade


def _detect_frontal_faces(frame, min_size=(60, 60)):
    """
    Detect front-facing faces with OpenCV. Returns list of (x, y, w, h) in frame.
    Only faces facing the camera (frontal) are detected.
    """
    cascade = _get_face_cascade()
    if cascade is None or frame is None or frame.size == 0:
        return []
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=min_size,
        flags=cv2.CASCADE_SCALE_IMAGE,
    )
    return list(faces)


# ---------- Person / face detection for driver camera (small YOLO) ----------
_person_model = None


def load_person_model():
    """Load small YOLO for person detection (yolov8n or train_models face/person). Used for driver snap camera."""
    global _person_model
    if _person_model is not None:
        return True
    root = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(root, "train_models", "person.pt"),
        os.path.join(root, "train_models", "face.pt"),
        os.path.join(root, "train_models", "yolov8n.pt"),
        "yolov8n.pt",
    ]
    try:
        from ultralytics import YOLO
        for path in candidates:
            if path == "yolov8n.pt":
                _person_model = YOLO("yolov8n.pt")
                break
            if os.path.isfile(path):
                _person_model = YOLO(path)
                break
        if _person_model is None:
            _person_model = YOLO("yolov8n.pt")
        dummy = np.zeros((320, 320, 3), dtype=np.uint8)
        _person_model.predict(dummy, conf=0.25, verbose=False)
        return True
    except Exception:
        return False


def detect_person(frame, conf_threshold=0.4):
    """
    Detect person (and optionally face if model has it). Draws bboxes on frame.
    Returns annotated_frame. Uses COCO class 0 = person.
    """
    if frame is None or frame.size == 0:
        return frame
    if not load_person_model():
        return frame
    try:
        results = _person_model.predict(
            frame,
            conf=conf_threshold,
            verbose=False,
            imgsz=480,
            classes=[0],
        )
    except Exception:
        return frame
    out = frame.copy()
    for result in results:
        if result.boxes is None:
            continue
        for i in range(len(result.boxes)):
            x1, y1, x2, y2 = result.boxes.xyxy[i].cpu().numpy()
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
            cv2.rectangle(out, (x1, y1), (x2, y2), (255, 200, 0), 2)
            cv2.putText(out, "Person", (x1, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2, cv2.LINE_AA)
    return out


def detect_person_and_crop(frame, conf_threshold=0.35):
    """
    Capture image for sidebar only when a face is detected (OpenCV frontal face).
    When only a person is detected (YOLO), do not capture — sidebar stays as last face capture.
    Returns (annotated_frame, crop_bgr or None). Crop is non-None only for face.
    """
    if frame is None or frame.size == 0:
        return frame, None
    h, w = frame.shape[:2]
    out = frame.copy()

    # 1) OpenCV frontal face: only then capture for sidebar
    faces = _detect_frontal_faces(frame, min_size=(50, 50))
    if len(faces) > 0:
        best = max(faces, key=lambda r: r[2] * r[3])
        x, y, fw, fh = best
        pad = max(12, int(0.2 * min(fw, fh)))
        x1p = max(0, x - pad)
        y1p = max(0, y - pad)
        x2p = min(w, x + fw + pad)
        y2p = min(h, y + fh + pad)
        if x2p > x1p and y2p > y1p:
            face_crop = frame[y1p:y2p, x1p:x2p]
            if face_crop.size > 0 and face_crop.shape[0] >= 40 and face_crop.shape[1] >= 40:
                cv2.rectangle(out, (x, y), (x + fw, y + fh), (0, 255, 0), 2)
                cv2.putText(out, "Face", (x, y - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)
                return out, face_crop

    # 2) YOLO person: draw only, do not capture (no crop to sidebar)
    if load_person_model():
        try:
            results = _person_model.predict(
                frame,
                conf=conf_threshold,
                verbose=False,
                imgsz=320,
                classes=[0],
            )
            for result in results:
                if result.boxes is None:
                    continue
                for i in range(len(result.boxes)):
                    x1, y1, x2, y2 = result.boxes.xyxy[i].cpu().numpy()
                    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                    cv2.rectangle(out, (x1, y1), (x2, y2), (255, 200, 0), 2)
                    cv2.putText(out, "Person", (x1, y1 - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2, cv2.LINE_AA)
        except Exception:
            pass
    return out, None
