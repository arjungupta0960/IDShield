# backend/mrz.py

import re


# ==========================================
# MRZ NORMALIZATION
# ==========================================

def normalize_mrz_line(line):
    """
    Clean OCR output so it can be analyzed as MRZ data.
    """

    if not line:
        return ""

    # Convert to uppercase
    line = line.upper()

    # Remove spaces
    line = line.replace(" ", "")

    # Keep only characters allowed in MRZ
    line = re.sub(r"[^A-Z0-9<]", "", line)

    return line


# ==========================================
# FIND MRZ LINES
# ==========================================

def find_mrz_lines(text_lines):
    """
    Find two passport TD3 MRZ lines from OCR output.

    TD3 passport MRZ:
        Line 1 = 44 characters
        Line 2 = 44 characters

    We allow OCR output to be slightly shorter during
    detection, but we do NOT pad it.
    """

    candidates = []

    for line in text_lines:

        cleaned = normalize_mrz_line(line)

        # MRZ usually contains many '<' characters.
        # Keep reasonably long candidates.
        if len(cleaned) >= 30 and "<" in cleaned:

            candidates.append(cleaned)

    # ------------------------------------------
    # Look for two consecutive MRZ-like lines
    # ------------------------------------------

    for i in range(len(candidates) - 1):

        line1 = candidates[i]
        line2 = candidates[i + 1]

        # Passport TD3 starts with P<
        if line1.startswith("P<"):

            # Second line should contain mostly
            # letters, digits and filler characters.
            if len(line2) >= 30:

                return line1, line2

    return None, None


# ==========================================
# VALIDATE MRZ STRUCTURE
# ==========================================

def validate_mrz_structure(line1, line2):
    """
    Validate basic TD3 MRZ structure.

    A standard TD3 passport MRZ contains:
        2 lines
        44 characters per line
    """

    errors = []

    # ------------------------------------------
    # Line 1
    # ------------------------------------------

    if len(line1) != 44:

        errors.append(
            f"MRZ line 1 has {len(line1)} characters; "
            f"expected 44."
        )

    # ------------------------------------------
    # Line 2
    # ------------------------------------------

    if len(line2) != 44:

        errors.append(
            f"MRZ line 2 has {len(line2)} characters; "
            f"expected 44."
        )

    # ------------------------------------------
    # Document type
    # ------------------------------------------

    if not line1.startswith("P<"):

        errors.append(
            "MRZ line 1 does not start with P<."
        )

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }


# ==========================================
# PARSE MRZ
# ==========================================

def parse_mrz(line1, line2):
    """
    Parse a TD3 passport MRZ.

    IMPORTANT:
    We do not pad incomplete MRZ lines.
    """

    # Normalize
    line1 = normalize_mrz_line(line1)
    line2 = normalize_mrz_line(line2)

    # ------------------------------------------
    # Validate structure first
    # ------------------------------------------

    structure = validate_mrz_structure(
        line1,
        line2
    )

    if not structure["valid"]:

        raise ValueError(
            "Invalid TD3 MRZ structure: "
            + " | ".join(
                structure["errors"]
            )
        )

    # ==========================================
    # LINE 1
    # ==========================================

    document_type = line1[0]

    issuing_country = line1[2:5]

    name_section = line1[5:44]

    # Split surname and given names
    name_parts = name_section.split("<<", 1)

    surname = (
        name_parts[0]
        .replace("<", " ")
        .strip()
    )

    given_names = ""

    if len(name_parts) > 1:

        given_names = (
            name_parts[1]
            .replace("<", " ")
            .strip()
        )

    # ==========================================
    # LINE 2
    # ==========================================

    passport_number = (
        line2[0:9]
        .replace("<", "")
    )

    passport_check_digit = line2[9]

    nationality = line2[10:13]

    date_of_birth = line2[13:19]

    dob_check_digit = line2[19]

    sex = line2[20]

    expiry_date = line2[21:27]

    expiry_check_digit = line2[27]

    optional_data = line2[28:42]

    final_check_digit = line2[43]

    # ==========================================
    # RETURN STRUCTURED DATA
    # ==========================================

    return {

        "document_type": document_type,

        "issuing_country": issuing_country,

        "surname": surname,

        "given_names": given_names,

        "passport_number": passport_number,

        "passport_check_digit": passport_check_digit,

        "nationality": nationality,

        "date_of_birth": date_of_birth,

        "dob_check_digit": dob_check_digit,

        "sex": sex,

        "expiry_date": expiry_date,

        "expiry_check_digit": expiry_check_digit,

        "optional_data": optional_data,

        "final_check_digit": final_check_digit,

        "raw_mrz": [
            line1,
            line2
        ]
    }