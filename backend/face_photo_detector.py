import io

import numpy as np
from PIL import Image

try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except Exception:
    face_recognition = None
    FACE_RECOGNITION_AVAILABLE = False


def _to_rgb_array(image_input):
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


def detect_document_face(image_input):
    """
    Detect the most prominent face in the uploaded document.

    This is document-photo detection, not identity verification.
    """

    if not FACE_RECOGNITION_AVAILABLE:
        return {
            "detected": False,
            "count": 0,
            "location": None,
            "face_image": None,
            "available": False
        }

    image = _to_rgb_array(image_input)
    locations = face_recognition.face_locations(image)

    if not locations:
        return {
            "detected": False,
            "count": 0,
            "location": None,
            "face_image": None,
            "available": True
        }

    locations = sorted(
        locations,
        key=lambda box: (box[2] - box[0]) * (box[1] - box[3]),
        reverse=True
    )

    top, right, bottom, left = locations[0]

    height, width = image.shape[:2]

    margin_y = max(10, int((bottom - top) * 0.25))
    margin_x = max(10, int((right - left) * 0.20))

    top = max(0, top - margin_y)
    bottom = min(height, bottom + margin_y)
    left = max(0, left - margin_x)
    right = min(width, right + margin_x)

    crop = Image.fromarray(
        image[top:bottom, left:right]
    )

    return {
        "detected": True,
        "count": len(locations),
        "location": (top, right, bottom, left),
        "face_image": crop,
        "available": True
    }