from PIL import Image
import io
import numpy as np


def calculate_image_hash(image_bytes, size=32):
    """
    Calculate a normalized average-hash for duplicate/similarity screening.
    """
    image = Image.open(io.BytesIO(image_bytes)).convert("L")
    image = image.resize((size, size))
    pixels = np.asarray(image, dtype=np.float32)

    average = pixels.mean()
    bits = pixels >= average

    # Store as a compact hexadecimal fingerprint.
    flat = bits.flatten()
    value = 0
    hex_chars = []

    for index, bit in enumerate(flat):
        value = (value << 1) | int(bit)

        if (index + 1) % 4 == 0:
            hex_chars.append(format(value, "x"))
            value = 0

    return "".join(hex_chars)


def hash_distance(hash_a, hash_b):
    if not hash_a or not hash_b or len(hash_a) != len(hash_b):
        return None

    distance = 0

    for a, b in zip(hash_a, hash_b):
        distance += (int(a, 16) ^ int(b, 16)).bit_count()

    return distance


def find_duplicate_screening(image_bytes, audit_records, threshold=80):
    """
    Compare the uploaded image against previous audit fingerprints.

    threshold is a Hamming-distance threshold. Lower means stricter.
    """
    current_hash = calculate_image_hash(image_bytes)

    best_match = None
    best_distance = None

    for record in audit_records:
        stored_hash = record.get("document_fingerprint")

        if not stored_hash:
            continue

        distance = hash_distance(current_hash, stored_hash)

        if distance is None:
            continue

        if best_distance is None or distance < best_distance:
            best_distance = distance
            best_match = record

    if best_match is not None and best_distance <= threshold:
        return {
            "status": "DUPLICATE",
            "matched": True,
            "distance": best_distance,
            "screening_id": best_match.get("screening_id"),
            "message": "A similar document image was previously screened."
        }

    return {
        "status": "NEW",
        "matched": False,
        "distance": best_distance,
        "screening_id": None,
        "message": "No similar previously screened document was detected."
    }
