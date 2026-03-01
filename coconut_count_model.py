"""
Coconut detection for counting cameras using YOLO model from train_models/.
Detects coconuts only and draws clear bounding boxes on frames for 6 cameras.
Uses GPU (CUDA) when available with FP16 and warmup for smooth, fast inference.
"""
import os
import cv2
import numpy as np

# Optional: ultralytics YOLO for coconut model
_model = None
_model_path = None

# Device: prefer CUDA GPU for smooth performance; fallback to CPU
_inference_device = None

# Inference settings: smaller imgsz = faster (480 is good balance for 20MB model)
IMGSZ = 480
# Use half precision on GPU for ~2x speed (minimal accuracy loss)
USE_HALF = True


def _get_device():
    """Return best available device: 'cuda' (GPU) if available, else 'cpu'."""
    global _inference_device
    if _inference_device is not None:
        return _inference_device
    try:
        import torch
        if torch.cuda.is_available():
            _inference_device = "cuda"  # or 0 for first GPU
        else:
            _inference_device = "cpu"
    except Exception:
        _inference_device = "cpu"
    return _inference_device

# Search order: train_models/coconut.pt, train_models/best.pt, then project root coconut.pt
def _get_model_path():
    global _model_path
    if _model_path is not None:
        return _model_path
    root = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(root, "train_models", "coconut.pt"),
        os.path.join(root, "train_models", "best.pt"),
        os.path.join(root, "train_models", "weights", "best.pt"),
        os.path.join(root, "coconut.pt"),
    ]
    for path in candidates:
        if os.path.isfile(path):
            _model_path = path
            return path
    _model_path = os.path.join(root, "train_models", "coconut.pt")
    return _model_path


def load_model():
    """Load YOLO coconut model once on GPU (CUDA) if available. Runs warmup so first real frame is fast."""
    global _model
    if _model is not None:
        return True
    try:
        from ultralytics import YOLO
    except ImportError:
        return False
    path = _get_model_path()
    if not os.path.isfile(path):
        return False
    try:
        _model = YOLO(path)
        device = _get_device()
        if device == "cuda":
            try:
                _model.to(device)
            except Exception:
                pass
        # Warmup: one dummy inference so first real frame doesn't pay for CUDA init / JIT
        try:
            warmup = np.zeros((IMGSZ, IMGSZ, 3), dtype=np.uint8)
            _model.predict(
                warmup,
                conf=0.25,
                iou=0.45,
                verbose=False,
                device=device,
                imgsz=IMGSZ,
                half=(USE_HALF and device == "cuda"),
            )
        except Exception:
            pass
        return True
    except Exception:
        return False


def detect_coconuts(frame, conf_threshold=0.25, iou_threshold=0.45):
    """
    Run coconut detection on a BGR frame.
    Returns (annotated_frame, count).
    Detects coconuts only; all other classes are ignored.
    Draws clear bounding boxes and labels for accurate counting.
    """
    if frame is None or frame.size == 0:
        return frame, 0

    if not load_model():
        return frame, 0

    device = _get_device()
    use_half = USE_HALF and device == "cuda"
    try:
        results = _model.predict(
            frame,
            conf=conf_threshold,
            iou=iou_threshold,
            verbose=False,
            device=device,
            imgsz=IMGSZ,
            half=use_half,
        )
    except Exception:
        return frame, 0

    count = 0
    out = frame.copy()
    h, w = out.shape[:2]

    for result in results:
        if result.boxes is None:
            continue
        boxes = result.boxes
        names = result.names or {}

        for i in range(len(boxes)):
            cls_id = int(boxes.cls[i].item())
            cls_name = (names.get(cls_id) or "").lower()
            if names and "coconut" not in cls_name:
                continue
            conf = float(boxes.conf[i].item())
            x1, y1, x2, y2 = boxes.xyxy[i].cpu().numpy()
            x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)

            # Beautiful bounding box only (no label) — shadow, main stroke, inner highlight
            box_w, box_h = x2 - x1, y2 - y1
            t = max(2, min(6, min(box_w, box_h) // 25))  # stroke thickness
            off = max(1, t // 2)  # shadow offset
            # 1) Soft shadow for depth (dark green, slightly offset)
            shadow = (0, 90, 50)  # BGR dark green
            cv2.rectangle(out, (x1 + off, y1 + off), (x2 + off, y2 + off), shadow, t + 1)
            # 2) Main box — vibrant green
            color = (0, 230, 120)  # BGR fresh green
            cv2.rectangle(out, (x1, y1), (x2, y2), color, t)
            # 3) Inner highlight for a crisp edge (1px inset)
            inset = max(1, t - 1)
            highlight = (180, 255, 200)  # BGR light green
            cv2.rectangle(out, (x1 + inset, y1 + inset), (x2 - inset, y2 - inset), highlight, 1)
            count += 1

    return out, count


def get_model_loaded():
    """Return whether the coconut model is loaded."""
    return _model is not None
