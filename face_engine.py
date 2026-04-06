"""
face_engine.py — Deep Learning Face Recognition Engine
Based on report Module 2 pipeline:
  Frame → Preprocessing → Segmentation → Feature Extraction → Classification-CNN
Uses dlib ResNet-34 model (128-d face embeddings) via face_recognition library.
"""
import cv2
import numpy as np
import face_recognition
import pickle

TOLERANCE = 0.50   # Euclidean distance threshold (lower = stricter)


def preprocess_frame(img_bytes: bytes) -> np.ndarray | None:
    """
    Module preprocessing pipeline:
      1. Decode bytes → BGR image
      2. Resize to standard dimensions
      3. Denoise (Gaussian Blur)
      4. Convert to RGB for face_recognition
    """
    arr = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if img is None:
        return None

    # Resize to max 640px wide (speed + consistency)
    h, w = img.shape[:2]
    if w > 640:
        scale = 640 / w
        img = cv2.resize(img, (640, int(h * scale)), interpolation=cv2.INTER_AREA)

    # Denoise — smooth unwanted noise
    img = cv2.GaussianBlur(img, (3, 3), 0)

    # BGR → RGB (face_recognition expects RGB)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def encode_face_from_bytes(img_bytes: bytes) -> np.ndarray | None:
    """
    Face Enrollment:
      Preprocess → Face Detection (HOG) → Feature Extraction (ResNet-128d)
    Returns 128-d encoding or None if no face detected.
    """
    rgb = preprocess_frame(img_bytes)
    if rgb is None:
        return None

    locations = face_recognition.face_locations(rgb, model="hog")
    if not locations:
        return None

    encodings = face_recognition.face_encodings(rgb, locations)
    return encodings[0] if encodings else None


def compare_faces(stored_blob: bytes, live_bytes: bytes) -> tuple[bool, float, np.ndarray | None]:
    """
    Module 3 — Prediction:
      Live frame → Preprocessing → Feature Extraction → 
      Euclidean Distance vs stored encoding → Accept/Reject
    
    Returns: (matched, confidence_percent, live_encoding)
    """
    stored_enc = pickle.loads(stored_blob)

    rgb = preprocess_frame(live_bytes)
    if rgb is None:
        return False, 0.0, None

    locations = face_recognition.face_locations(rgb, model="hog")
    encodings = face_recognition.face_encodings(rgb, locations)

    if not encodings:
        return False, 0.0, None

    live_enc = encodings[0]
    distance = face_recognition.face_distance([stored_enc], live_enc)[0]
    confidence = round((1.0 - distance) * 100, 2)
    matched = distance <= TOLERANCE

    return matched, confidence, live_enc
