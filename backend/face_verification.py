import io

import numpy as np
from PIL import Image

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except Exception:
    face_recognition = None
    FACE_RECOGNITION_AVAILABLE = False


def load_image(image_input):
    """Convert uploaded image bytes or an image array to RGB numpy data."""
    if isinstance(image_input, (bytes, bytearray)):
        image = Image.open(io.BytesIO(image_input)).convert("RGB")
        return np.array(image)

    if isinstance(image_input, Image.Image):
        return np.array(image_input.convert("RGB"))

    array = np.asarray(image_input)

    if array.ndim == 2:
        return np.stack([array] * 3, axis=-1)

    if array.ndim == 3 and array.shape[2] == 4:
        return array[:, :, :3]

    return array


def detect_faces(image):
    if not FACE_RECOGNITION_AVAILABLE:
        return []

    image = load_image(image)
    return face_recognition.face_locations(image)


def get_face_encoding(image):
    if not FACE_RECOGNITION_AVAILABLE:
        return None

    image = load_image(image)
    locations = detect_faces(image)

    if not locations:
        return None

    encodings = face_recognition.face_encodings(
        image,
        known_face_locations=locations
    )

    if not encodings:
        return None

    return encodings[0]


def compare_faces(reference_image, passport_image):
    """
    Compare the first detected face in each image.

    Inputs may be uploaded bytes, PIL images, or numpy arrays.
    """

    if not FACE_RECOGNITION_AVAILABLE:
        return {
            "status": "REVIEW",
            "score": 0.0,
            "distance": None,
            "message": "Face verification is unavailable in this deployment."
        }

    reference_encoding = get_face_encoding(reference_image)
    passport_encoding = get_face_encoding(passport_image)

    if reference_encoding is None:
        return {
            "status": "REVIEW",
            "score": 0.0,
            "distance": None,
            "message": "No face detected in reference image."
        }

    if passport_encoding is None:
        return {
            "status": "REVIEW",
            "score": 0.0,
            "distance": None,
            "message": "No face detected in passport image."
        }

    distance = float(
        face_recognition.face_distance(
            [reference_encoding],
            passport_encoding
        )[0]
    )

    score = max(
        0.0,
        min(100.0, (1 - distance) * 100)
    )

    if distance <= 0.45:
        status = "PASS"
        message = "Faces are highly similar."
    elif distance <= 0.60:
        status = "REVIEW"
        message = (
            "Faces have moderate similarity. "
            "Manual review recommended."
        )
    else:
        status = "FAIL"
        message = "Faces appear significantly different."

    return {
        "status": status,
        "score": round(score, 2),
        "distance": round(distance, 4),
        "message": message
    }