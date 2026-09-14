import io

import cv2
import numpy as np
from PIL import Image


# ============================================================
# MODEL PATHS
# ============================================================

YUNET_MODEL = "models/face_detection_yunet_2023mar.onnx"
SFACE_MODEL = "models/face_recognition_sface_2021dec.onnx"


# ============================================================
# MODEL LOADERS
# ============================================================

_detector = None
_recognizer = None


def get_face_detector():
    """Load YuNet face detector once."""
    global _detector

    if _detector is None:
        _detector = cv2.FaceDetectorYN.create(
            YUNET_MODEL,
            "",
            (320, 320),
            0.6,
            0.3,
            5000
        )

    return _detector


def get_face_recognizer():
    """Load SFace face recognizer once."""
    global _recognizer

    if _recognizer is None:
        _recognizer = cv2.FaceRecognizerSF.create(
            SFACE_MODEL,
            ""
        )

    return _recognizer


# ============================================================
# IMAGE CONVERSION
# ============================================================

def load_image(image_input):
    """Convert bytes/PIL/numpy input into RGB numpy image."""

    if isinstance(image_input, (bytes, bytearray)):
        image = Image.open(
            io.BytesIO(image_input)
        ).convert("RGB")

        return np.array(image)

    if isinstance(image_input, Image.Image):
        return np.array(
            image_input.convert("RGB")
        )

    array = np.asarray(image_input)

    if array.ndim == 2:
        return np.stack(
            [array] * 3,
            axis=-1
        )

    if array.ndim == 3 and array.shape[2] == 4:
        return array[:, :, :3]

    return array


# ============================================================
# FACE DETECTION
# ============================================================

def detect_faces(image):
    """
    Detect faces using OpenCV YuNet.

    Returns a list of face bounding boxes.
    """

    image = load_image(image)

    if image is None or image.size == 0:
        return []

    detector = get_face_detector()

    height, width = image.shape[:2]

    detector.setInputSize(
        (width, height)
    )

    # YuNet expects BGR
    bgr = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2BGR
    )

    _, detections = detector.detect(bgr)

    if detections is None:
        return []

    faces = []

    for detection in detections:
        x, y, w, h = detection[:4]

        faces.append({
            "x": int(max(0, x)),
            "y": int(max(0, y)),
            "w": int(max(0, w)),
            "h": int(max(0, h)),
            "confidence": float(detection[-1])
        })

    return faces


# ============================================================
# FACE EMBEDDING
# ============================================================

def get_face_embedding(image):
    """
    Detect the largest face and generate an SFace embedding.

    Returns:
        embedding or None
    """

    image = load_image(image)

    faces = detect_faces(image)

    if not faces:
        return None

    # Select largest face
    face = max(
        faces,
        key=lambda f: f["w"] * f["h"]
    )

    detector = get_face_detector()
    recognizer = get_face_recognizer()

    height, width = image.shape[:2]

    detector.setInputSize(
        (width, height)
    )

    bgr = cv2.cvtColor(
        image,
        cv2.COLOR_RGB2BGR
    )

    _, detections = detector.detect(bgr)

    if detections is None:
        return None

    # Find corresponding detection
    best_detection = None
    best_area = 0

    for detection in detections:
        x, y, w, h = detection[:4]

        area = max(0, w) * max(0, h)

        if area > best_area:
            best_area = area
            best_detection = detection

    if best_detection is None:
        return None

    aligned_face = recognizer.alignCrop(
        bgr,
        best_detection
    )

    embedding = recognizer.feature(
        aligned_face
    )

    return embedding


# ============================================================
# FACE COMPARISON
# ============================================================

def compare_faces(reference_image, passport_image):
    """
    Compare faces using OpenCV SFace.

    Inputs may be:
        - uploaded bytes
        - PIL images
        - numpy arrays
    """

    try:
        reference_embedding = get_face_embedding(
            reference_image
        )

        passport_embedding = get_face_embedding(
            passport_image
        )

    except Exception as e:
        return {
            "status": "REVIEW",
            "score": 0.0,
            "distance": None,
            "message": (
                "Face verification was unavailable: "
                + str(e)
            )
        }

    if reference_embedding is None:
        return {
            "status": "REVIEW",
            "score": 0.0,
            "distance": None,
            "message": (
                "No face detected in reference image."
            )
        }

    if passport_embedding is None:
        return {
            "status": "REVIEW",
            "score": 0.0,
            "distance": None,
            "message": (
                "No face detected in passport image."
            )
        }

    recognizer = get_face_recognizer()

    similarity = float(
        recognizer.match(
            reference_embedding,
            passport_embedding,
            cv2.FaceRecognizerSF_FR_COSINE
        )
    )

    # OpenCV SFace cosine similarity:
    #
    # >= 0.363 → same identity candidate
    #
    # We use a more conservative three-level
    # screening interpretation.

    if similarity >= 0.50:
        status = "PASS"
        message = (
            "Faces show high similarity."
        )

    elif similarity >= 0.363:
        status = "REVIEW"
        message = (
            "Faces show moderate similarity. "
            "Manual review recommended."
        )

    else:
        status = "FAIL"
        message = (
            "Faces show low similarity."
        )

    # Convert similarity into a 0–100 display score.
    score = max(
        0.0,
        min(
            100.0,
            similarity * 100.0
        )
    )

    return {
        "status": status,
        "score": round(score, 2),
        "similarity": round(similarity, 4),
        "distance": round(
            1.0 - similarity,
            4
        ),
        "message": message
    }