from PIL import Image, ImageChops, ImageEnhance
import io
import cv2
import numpy as np


def perform_ela(image_bytes, quality=90):
    original = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    buffer = io.BytesIO()
    original.save(buffer, format="JPEG", quality=quality)
    buffer.seek(0)
    compressed = Image.open(buffer).convert("RGB")

    difference = ImageChops.difference(original, compressed)
    extrema = difference.getextrema()
    max_difference = max(
        channel_max for channel_min, channel_max in extrema
    )

    scale = 1 if max_difference == 0 else 255 / max_difference
    ela_image = ImageEnhance.Brightness(difference).enhance(scale)

    grayscale = ela_image.convert("L")
    histogram = grayscale.histogram()
    total_pixels = sum(histogram)
    weighted_sum = sum(
        value * count for value, count in enumerate(histogram)
    )
    mean_error = (
        weighted_sum / total_pixels
        if total_pixels > 0 else 0
    )

    return ela_image, mean_error, max_difference


def calculate_tampering_score(mean_error, max_error):
    mean_component = min(mean_error / 50, 1.0)
    max_component = min(max_error / 255, 1.0)
    score = mean_component * 70 + max_component * 30
    return round(min(score, 100), 2)


def classify_tampering(score):
    if score < 20:
        return {
            "status": "PASS",
            "label": "LOW SUSPICION",
            "message": "No strong image-level tampering signal detected."
        }
    elif score < 45:
        return {
            "status": "REVIEW",
            "label": "MODERATE SUSPICION",
            "message": "Some image regions show elevated compression differences."
        }

    return {
        "status": "FAIL",
        "label": "HIGH SUSPICION",
        "message": "Significant image-level differences detected. Manual review recommended."
    }


def detect_suspicious_regions(ela_image, threshold_percentile=98.0,
                              min_area_ratio=0.001, max_regions=10):
    """
    Detect localized high-error regions in the ELA image.

    This is a screening heuristic, not proof of manipulation.
    Returns an annotated image and region metadata.
    """
    image = np.array(ela_image.convert("RGB"))
    gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

    threshold = float(np.percentile(gray, threshold_percentile))
    _, mask = cv2.threshold(
        gray, max(10, int(threshold)), 255, cv2.THRESH_BINARY
    )

    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

    height, width = gray.shape
    min_area = max(50, int(height * width * min_area_ratio))

    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    regions = []
    annotated = image.copy()

    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue

        x, y, w, h = cv2.boundingRect(contour)
        regions.append({
            "x": int(x),
            "y": int(y),
            "width": int(w),
            "height": int(h),
            "area": int(area)
        })

    regions.sort(key=lambda r: r["area"], reverse=True)
    regions = regions[:max_regions]

    for index, region in enumerate(regions, start=1):
        x = region["x"]
        y = region["y"]
        w = region["width"]
        h = region["height"]

        cv2.rectangle(
            annotated,
            (x, y),
            (x + w, y + h),
            (255, 255, 255),
            3
        )
        cv2.putText(
            annotated,
            f"Region {index}",
            (x, max(20, y - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )

    return Image.fromarray(annotated), regions, threshold
