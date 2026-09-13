import re
from datetime import datetime


LABELS = {
    "passport_number": [
        "PASSPORT NO.",
        "PASSPORT NO",
        "PASSPORT NUMBER",
    ],
    "surname": ["SURNAME"],
    "given_names": ["GIVEN NAMES", "GIVEN NAME"],
    "nationality": ["NATIONALITY"],
    "date_of_birth": ["DATE OF BIRTH", "BIRTH"],
    "sex": ["SEX", "GENDER"],
    "date_of_issue": ["DATE OF ISSUE", "ISSUE"],
    "date_of_expiry": [
        "DATE OF EXPIRY",
        "EXPIRY DATE",
        "EXPIRY",
    ],
    "place_of_birth": ["PLACE OF BIRTH"],
    "place_of_issue": ["PLACE OF ISSUE"],
}


def clean_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text).strip())


def _normal_label(text):
    return (
        clean_text(text)
        .upper()
        .replace(":", "")
        .strip()
    )


def _looks_like_label(text):
    normalized = _normal_label(text)
    return any(
        normalized == label
        for labels in LABELS.values()
        for label in labels
    )


def _extract_inline_value(line, labels):
    upper = line.upper()

    for label in sorted(labels, key=len, reverse=True):
        position = upper.find(label)

        if position == -1:
            continue

        value = line[position + len(label):]
        value = re.sub(r"^[\s:.\-]+", "", value).strip()

        if value:
            return value

    return None


def _get_field(lines, labels):
    # First: label and value on the same OCR line.
    for line in lines:
        value = _extract_inline_value(line, labels)
        if value:
            return value

    # Second: label and value are separate OCR lines.
    normalized_labels = {
        _normal_label(label) for label in labels
    }

    for index, line in enumerate(lines):
        if _normal_label(line) not in normalized_labels:
            continue

        for candidate in lines[index + 1:index + 4]:
            if not candidate:
                continue
            if _looks_like_label(candidate):
                break
            if len(candidate) <= 80:
                return candidate

    return None


def normalize_passport_number(value):
    if not value:
        return None

    value = re.sub(r"[^A-Z0-9]", "", value.upper())

    if len(value) < 6:
        return None

    # Conservative OCR correction only for the passport-number field.
    return value


def normalize_date(value):
    if not value:
        return None

    value = clean_text(value).upper()

    # DD.MM.YYYY / DD-MM-YYYY / DD/MM/YYYY
    match = re.search(
        r"\b(\d{2})[./-](\d{2})[./-](\d{4})\b",
        value
    )
    if match:
        day, month, year = match.groups()
        return f"{day}.{month}.{year}"

    # DD MON YYYY, e.g. 01 JAN 1990
    match = re.search(
        r"\b(\d{1,2})\s+"
        r"(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)"
        r"\s+(\d{4})\b",
        value
    )

    if match:
        day, month_text, year = match.groups()

        month = datetime.strptime(
            month_text,
            "%b"
        ).month

        return f"{int(day):02d}.{month:02d}.{year}"

    # DDMMYYYY
    match = re.search(r"\b(\d{2})(\d{2})(\d{4})\b", value)
    if match:
        day, month, year = match.groups()
        return f"{day}.{month}.{year}"

    return None


def extract_document_fields(text_lines):
    """
    Extract structured visible-document fields from OCR.

    OCR layouts vary, so this parser supports both:
      Label: VALUE
    and:
      Label
      VALUE

    MRZ remains the authoritative machine-readable source.
    """
    empty = {
        "passport_number": None,
        "surname": None,
        "given_names": None,
        "nationality": None,
        "date_of_birth": None,
        "sex": None,
        "date_of_issue": None,
        "date_of_expiry": None,
        "place_of_birth": None,
        "place_of_issue": None,
    }

    if not text_lines:
        return empty

    lines = [
        clean_text(line)
        for line in text_lines
        if clean_text(line)
    ]

    # Do not interpret MRZ lines as visible fields.
    lines = [
        line for line in lines
        if len(line.replace(" ", "")) != 44
    ]

    result = {}

    result["passport_number"] = normalize_passport_number(
        _get_field(lines, LABELS["passport_number"])
    )

    for field in [
        "surname",
        "given_names",
        "place_of_birth",
        "place_of_issue",
    ]:
        value = _get_field(lines, LABELS[field])
        result[field] = value.upper().strip() if value else None

    nationality = _get_field(
        lines,
        LABELS["nationality"]
    )

    if nationality:
        nationality = nationality.upper()
        if "IND" in nationality or "INDIAN" in nationality:
            nationality = "IND"
    result["nationality"] = nationality

    result["sex"] = (
        _get_field(lines, LABELS["sex"]) or ""
    ).upper().strip() or None

    if result["sex"]:
        match = re.search(r"\b([MF])\b", result["sex"])
        result["sex"] = match.group(1) if match else result["sex"]

    for field in [
        "date_of_birth",
        "date_of_issue",
        "date_of_expiry",
    ]:
        result[field] = normalize_date(
            _get_field(lines, LABELS[field])
        )

    return result
