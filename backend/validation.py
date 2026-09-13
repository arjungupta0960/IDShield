from datetime import datetime


# ==========================================
# ICAO MRZ CHARACTER VALUE
# ==========================================

def char_value(char):
    """
    ICAO 9303 character values:

    0-9 -> 0-9
    A-Z -> 10-35
    <   -> 0
    """

    if char == "<":
        return 0

    if "0" <= char <= "9":
        return int(char)

    if "A" <= char <= "Z":
        return ord(char) - ord("A") + 10

    return 0


# ==========================================
# ICAO CHECK DIGIT
# ==========================================

def calculate_check_digit(value):
    """
    ICAO MRZ check digit.

    Repeating weights:
    7, 3, 1
    """

    weights = [7, 3, 1]

    total = 0

    for i, char in enumerate(value):
        total += char_value(char) * weights[i % 3]

    return total % 10


# ==========================================
# NORMALIZE MRZ
# ==========================================

def normalize_mrz_line(line):
    if not line:
        return ""

    return (
        line.upper()
        .replace(" ", "")
        .replace("\n", "")
        .replace("\r", "")
    )


# ==========================================
# VALIDATE MRZ CHECKSUMS
# ==========================================

def validate_mrz(line2):
    """
    Validate ICAO TD3 Passport MRZ Line 2.

    Positions:

    1-9    Passport number
    10     Passport number check digit

    11-13  Nationality

    14-19  Date of birth
    20     DOB check digit

    21     Sex

    22-27  Expiry date
    28     Expiry check digit

    29-42  Optional data
    43     Optional data check digit

    44     Composite check digit
    """

    line2 = normalize_mrz_line(line2)

    # --------------------------------------
    # Structure check
    # --------------------------------------

    if len(line2) != 44:

        return {
            "passport_number": False,
            "date_of_birth": False,
            "expiry_date": False,
            "optional_data": False,
            "composite": False,
        }

    try:

        # ----------------------------------
        # Passport number
        # ----------------------------------

        passport_number = line2[0:9]

        passport_check_digit = int(
            line2[9]
        )

        calculated_passport_check = (
            calculate_check_digit(
                passport_number
            )
        )

        passport_valid = (
            calculated_passport_check
            == passport_check_digit
        )


        # ----------------------------------
        # Date of birth
        # ----------------------------------

        date_of_birth = line2[13:19]

        dob_check_digit = int(
            line2[19]
        )

        calculated_dob_check = (
            calculate_check_digit(
                date_of_birth
            )
        )

        dob_valid = (
            calculated_dob_check
            == dob_check_digit
        )


        # ----------------------------------
        # Expiry date
        # ----------------------------------

        expiry_date = line2[21:27]

        expiry_check_digit = int(
            line2[27]
        )

        calculated_expiry_check = (
            calculate_check_digit(
                expiry_date
            )
        )

        expiry_valid = (
            calculated_expiry_check
            == expiry_check_digit
        )


        # ----------------------------------
        # Optional data
        # ----------------------------------

        optional_data = line2[28:42]

        optional_check_digit = int(
            line2[42]
        )

        calculated_optional_check = (
            calculate_check_digit(
                optional_data
            )
        )

        optional_valid = (
            calculated_optional_check
            == optional_check_digit
        )


        # ----------------------------------
        # Composite check
        # ----------------------------------

        composite_data = (
            line2[0:10]
            + line2[13:20]
            + line2[21:28]
            + line2[28:43]
        )

        composite_check_digit = int(
            line2[43]
        )

        calculated_composite_check = (
            calculate_check_digit(
                composite_data
            )
        )

        composite_valid = (
            calculated_composite_check
            == composite_check_digit
        )


        # ----------------------------------
        # Return results
        # ----------------------------------

        return {

            "passport_number":
                passport_valid,

            "date_of_birth":
                dob_valid,

            "expiry_date":
                expiry_valid,

            "optional_data":
                optional_valid,

            "composite":
                composite_valid,
        }

    except (ValueError, TypeError):

        return {

            "passport_number": False,

            "date_of_birth": False,

            "expiry_date": False,

            "optional_data": False,

            "composite": False,
        }


# ==========================================
# TEXT NORMALIZATION
# ==========================================

def normalize_text(value):
    if value is None:
        return ""

    return (
        str(value)
        .upper()
        .replace("<", " ")
        .strip()
    )


# ==========================================
# NAME NORMALIZATION
# ==========================================

def normalize_name(value):
    if value is None:
        return ""

    value = normalize_text(value)

    return " ".join(
        value.split()
    )


# ==========================================
# VALUE COMPARISON
# ==========================================

def compare_values(document_value, mrz_value):

    if not document_value:
        return None

    document_value = normalize_text(
        document_value
    )

    mrz_value = normalize_text(
        mrz_value
    )

    if not document_value or not mrz_value:
        return None

    return document_value == mrz_value


# ==========================================
# DOCUMENT CONSISTENCY VALIDATION
# ==========================================

def validate_document(
    document_data,
    mrz_data
):
    """
    Compare visible document OCR values
    against parsed MRZ values.

    Result:
    True  -> match
    False -> mismatch
    None  -> OCR value unavailable
    """

    results = {}


    # --------------------------------------
    # Passport Number
    # --------------------------------------

    results["Passport Number"] = compare_values(
        document_data.get("passport_number"),
        mrz_data.get("passport_number")
    )


    # --------------------------------------
    # Date of Birth
    # --------------------------------------

    results["Date of Birth"] = compare_values(
        document_data.get("date_of_birth"),
        mrz_data.get("date_of_birth")
    )


    # --------------------------------------
    # Expiry Date
    # --------------------------------------

    results["Expiry Date"] = compare_values(
        document_data.get("expiry_date"),
        mrz_data.get("expiry_date")
    )


    # --------------------------------------
    # Nationality
    # --------------------------------------

    results["Nationality"] = compare_values(
        document_data.get("nationality"),
        mrz_data.get("nationality")
    )


    # --------------------------------------
    # Sex
    # --------------------------------------

    results["Sex"] = compare_values(
        document_data.get("sex"),
        mrz_data.get("sex")
    )


    # --------------------------------------
    # Surname
    # --------------------------------------

    document_surname = (
        document_data.get("surname")
    )

    mrz_surname = (
        mrz_data.get("surname")
    )

    if document_surname:

        results["Surname"] = (
            normalize_name(
                document_surname
            )
            ==
            normalize_name(
                mrz_surname
            )
        )

    else:

        results["Surname"] = None


    # --------------------------------------
    # Given Names
    # --------------------------------------

    document_given_names = (
        document_data.get("given_names")
    )

    mrz_given_names = (
        mrz_data.get("given_names")
    )

    if document_given_names:

        results["Given Names"] = (
            normalize_name(
                document_given_names
            )
            ==
            normalize_name(
                mrz_given_names
            )
        )

    else:

        results["Given Names"] = None


    return results


# ==========================================
# EXPIRY VALIDATION
# ==========================================

def check_expiry(expiry_date):

    if not expiry_date:
        return {
            "valid": False,
            "message": "Expiry date unavailable"
        }

    try:

        date_object = datetime.strptime(
            expiry_date,
            "%y%m%d"
        )

        today = datetime.today()

        # MRZ two-digit year handling
        if date_object.year < 1970:

            date_object = date_object.replace(
                year=date_object.year + 100
            )

        if date_object.date() >= today.date():

            return {
                "valid": True,
                "message":
                    f"Document valid until "
                    f"{date_object.strftime('%d %b %Y')}"
            }

        else:

            return {
                "valid": False,
                "message":
                    f"Document expired on "
                    f"{date_object.strftime('%d %b %Y')}"
            }

    except ValueError:

        return {
            "valid": False,
            "message": "Invalid expiry date format"
        }