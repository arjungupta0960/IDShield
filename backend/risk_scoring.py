def calculate_risk_score(
    mrz_checks,
    consistency_results,
    expiry_result,
    tampering_result,
    face_result=None,
    duplicate_result=None
):
    score = 0
    reasons = []

    mrz_weights = {
        "passport_number": 10,
        "date_of_birth": 5,
        "expiry_date": 5,
        "optional_data": 2,
        "composite": 8
    }

    for check, weight in mrz_weights.items():
        if mrz_checks.get(check) is False:
            score += weight
            reasons.append(f"MRZ check failed: {check}")

    consistency_weights = {
        "Passport Number": 12,
        "Date of Birth": 6,
        "Expiry Date": 6,
        "Nationality": 2,
        "Sex": 2,
        "Surname": 1,
        "Given Names": 1
    }

    for field, weight in consistency_weights.items():
        if consistency_results.get(field) is False:
            score += weight
            reasons.append(f"Visible/MRZ mismatch: {field}")

    if tampering_result:
        status = tampering_result.get("status")
        if status == "FAIL":
            score += 25
            reasons.append("High image-level tampering suspicion.")
        elif status == "REVIEW":
            score += 12
            reasons.append("Moderate image-level tampering suspicion.")

    if expiry_result and expiry_result.get("valid") is False:
        score += 10
        reasons.append("Passport is expired or expiry is invalid.")

    if face_result:
        status = face_result.get("status")
        if status == "FAIL":
            score += 5
            reasons.append("Face verification failed.")
        elif status == "REVIEW":
            score += 2
            reasons.append("Face verification requires review.")

    if duplicate_result and duplicate_result.get("matched"):
        score += 20
        reasons.append("Similar document image was previously screened.")

    score = min(score, 100)

    if score < 20:
        level = "LOW"
    elif score < 50:
        level = "MEDIUM"
    elif score < 75:
        level = "HIGH"
    else:
        level = "CRITICAL"

    return {
        "score": score,
        "level": level,
        "reasons": reasons
    }
