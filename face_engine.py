"""
face_engine.py — Deep Learning Face Recognition Engine
Enhanced Version:
  - CLAHE (Contrast Limited Adaptive Histogram Equalization) for lighting robustness.
  - Laplacian Blur Detection for anti-spoofing/quality control.
  - Jittered Feature Extraction (ResNet-128d) for enrollment.
"""
import cv2
import numpy as np
import face_recognition
import pickle

# --- Configuration ---
TOLERANCE = 0.50             # Euclidean distance (lower = stricter, 0.6 is default)
BLUR_THRESHOLD = 50.0        # Laplacian variance (lower = blurrier)
ENROLL_JITTERS = 10          # Higher = more accurate registration (slower)
VERIFY_JITTERS = 1           # Lower = faster verification


def preprocess_frame(img_bytes: bytes) -> np.ndarray | None:
    """
    Preprocessing pipeline:
      1. Decode bytes → BGR image
      2. Resize (640px max)
      3. Global Contrast Enhancement (CLAHE on L-channel)
      4. Soft Denoising
    """
    arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None

    # 1. Resize for performance
    h, w = img.shape[:2]
    if w > 640:
        scale = 640 / w
        img = cv2.resize(img, (640, int(h * scale)), interpolation=cv2.INTER_AREA)

    # 2. Lighting Robustness: CLAHE (Contrast Limited Adaptive Histogram Equalization)
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    cl = clahe.apply(l)
    img_enhanced = cv2.merge((cl, a, b))
    img_enhanced = cv2.cvtColor(img_enhanced, cv2.COLOR_LAB2BGR)

    # 3. Denoise (Gaussian)
    img_final = cv2.GaussianBlur(img_enhanced, (3, 3), 0)

    # BGR → RGB
    return cv2.cvtColor(img_final, cv2.COLOR_BGR2RGB)


def is_lively(rgb_img: np.ndarray) -> tuple[bool, str]:
    """
    Quality and Liveness check:
    - Check if the image is too blurry.
    - Check if lighting is sufficient.
    """
    gray = cv2.cvtColor(rgb_img, cv2.COLOR_RGB2GRAY)
    
    # 1. Blur Detection (Laplacian Variance)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    if variance < BLUR_THRESHOLD:
        return False, "Image too blurry / Potential spoof detected."

    # 2. Brightness check
    brightness = np.mean(gray)
    if brightness < 40:
        return False, "Environment too dark."
    if brightness > 250:
        return False, "Environment too bright."

    return True, "Quality OK"


def encode_face_from_bytes(img_bytes: bytes) -> np.ndarray | None:
    """
    Face Enrollment (Admin side):
    Uses HOG detection + Jittered ResNet extraction for high accuracy registration.
    """
    rgb = preprocess_frame(img_bytes)
    if rgb is None:
        return None

    locations = face_recognition.face_locations(rgb, model="hog")
    if not locations:
        return None

    # Extraction with Jitter
    encodings = face_recognition.face_encodings(rgb, locations, num_jitters=ENROLL_JITTERS)
    return encodings[0] if encodings else None


def compare_faces(stored_blob: bytes, live_bytes: bytes) -> tuple[bool, float, np.ndarray | None, tuple[bool, str]]:
    """
    Face Prediction (User side):
    Returns: (matched, confidence_percent, live_encoding, quality_result)
    quality_result is (is_ok: bool, message: str)
    """
    try:
        stored_enc = pickle.loads(stored_blob)
    except Exception:
        return False, 0.0, None, (False, "Stored encoding corrupt")

    rgb = preprocess_frame(live_bytes)
    if rgb is None:
        return False, 0.0, None, (False, "Could not decode frame")

    # Quality Check
    lively, q_msg = is_lively(rgb)

    locations = face_recognition.face_locations(rgb, model="hog")
    if not locations:
        return False, 0.0, None, (False, "No face detected in frame")

    encodings = face_recognition.face_encodings(rgb, locations, num_jitters=VERIFY_JITTERS)
    if not encodings:
        return False, 0.0, None, (False, "Processing error")

    live_enc = encodings[0]
    distance = face_recognition.face_distance([stored_enc], live_enc)[0]
    
    # Confidence calculation
    confidence = round(max(0, (1.0 - distance)) * 100, 2)
    matched = distance <= TOLERANCE

    return matched, confidence, live_enc, (lively, q_msg)
