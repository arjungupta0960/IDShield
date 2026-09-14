import io

import cv2
import numpy as np
from PIL import Image


YUNET_MODEL = "models/face_detection_yunet_2023mar.onnx"

_detector = None


def get_face_detector():
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


def _to_rgb_array(image_input):
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


def detect_document_face(image_input):
    """
    Detect the most prominent face in the uploaded document.

    Returns:
        detected
        count
        location
        face_image
        available
    """

    try:
        image = _to_rgb_array(image_input)

        if image is None or image.size == 0:
            return {
                "detected": False,
                "count": 0,
                "location": None,
                "face_image": None,
                "available": True
            }

        detector = get_face_detector()

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
            return {
                "detected": False,
                "count": 0,
                "location": None,
                "face_image": None,
                "available": True
            }

        # Convert detections to a simpler structure.
        faces = []

        for detection in detections:
            x, y, w, h = detection[:4]

            faces.append({
                "x": int(max(0, x)),
                "y": int(max(0, y)),
                "w": int(max(0, w)),
                "h": int(max(0, h)),
                "confidence": float(detection[-1]),
                "raw": detection
            })

        if not faces:
            return {
                "detected": False,
                "count": 0,
                "location": None,
                "face_image": None,
                "available": True
            }

        # Largest face = most likely passport photograph.
        face = max(
            faces,
            key=lambda f: f["w"] * f["h"]
        )

        x = face["x"]
        y = face["y"]
        w = face["w"]
        h = face["h"]

        # Add margin.
        margin_y = max(
            10,
            int(h * 0.25)
        )

        margin_x = max(
            10,
            int(w * 0.20)
        )

        top = max(
            0,
            y - margin_y
        )

        bottom = min(
            height,
            y + h + margin_y
        )

        left = max(
            0,
            x - margin_x
        )

        right = min(
            width,
            x + w + margin_x
        )

        crop = Image.fromarray(
            image[top:bottom, left:right]
        )

        return {
            "detected": True,
            "count": len(faces),
            "location": (
                top,
                right,
                bottom,
                left
            ),
            "face_image": crop,
            "available": True
        }

    except Exception as e:
        return {
            "detected": False,
            "count": 0,
            "location": None,
            "face_image": None,
            "available": False,
            "error": str(e)
        }