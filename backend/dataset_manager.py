from datasets import load_dataset

from backend.mrz import parse_mrz


DATASET_NAME = "ud-synthetic/indian-passports"


def load_passport_dataset():
    """
    Load the synthetic Indian passport dataset
    from Hugging Face.
    """
    dataset = load_dataset(DATASET_NAME)
    return dataset["train"]


def _clean(value):
    """
    Safely convert a dataset value to a clean string.
    """
    if value is None:
        return ""

    return str(value).strip().strip('"')


def _extract_mrz_lines(record):
    """
    Recover MRZ lines from the malformed public dataset structure.

    The dataset currently stores the first 9 fields in
    __index_level_0__ and the remaining fields in another
    semicolon-separated column.

    We locate the MRZ by looking for:
        P<...
        passport-number + check digit + country + DOB...
    """

    index_data = _clean(
        record.get("__index_level_0__", "")
    )

    main_keys = [
        key
        for key in record.keys()
        if key != "__index_level_0__"
    ]

    if not main_keys:
        return None, None

    main_data = _clean(
        record.get(main_keys[0], "")
    )

    index_values = (
        index_data.split(";")
        if index_data
        else []
    )

    main_values = (
        main_data.split(";")
        if main_data
        else []
    )

    all_values = index_values + main_values

    # --------------------------------------------------
    # Find MRZ line 1
    # --------------------------------------------------

    mrz_line1 = None

    for value in all_values:
        value = _clean(value)

        if value.startswith("P<") and len(value) >= 30:
            mrz_line1 = value
            break

    # --------------------------------------------------
    # Find MRZ line 2
    # --------------------------------------------------

    mrz_line2 = None

    for value in all_values:
        value = _clean(value)

        # Passport MRZ line 2 normally starts with
        # passport number and contains the nationality.
        if (
            len(value) >= 40
            and "IND" in value
            and value != mrz_line1
        ):
            mrz_line2 = value
            break

    return mrz_line1, mrz_line2


def parse_record(record):
    """
    Convert one raw dataset record into a normalized
    passport dictionary.

    MRZ information is treated as the authoritative
    identity information.
    """

    mrz_line1, mrz_line2 = _extract_mrz_lines(record)

    if not mrz_line1 or not mrz_line2:
        raise ValueError(
            "Could not locate valid MRZ lines."
        )

    # --------------------------------------------------
    # Parse MRZ using our existing MRZ parser
    # --------------------------------------------------

    try:
        mrz_data = parse_mrz(
            mrz_line1,
            mrz_line2
        )
    except Exception as error:
        raise ValueError(
            f"MRZ parsing failed: {error}"
        )

    # --------------------------------------------------
    # Extract the other dataset values
    # --------------------------------------------------

    index_data = _clean(
        record.get("__index_level_0__", "")
    )

    main_keys = [
        key
        for key in record.keys()
        if key != "__index_level_0__"
    ]

    main_data = ""

    if main_keys:
        main_data = _clean(
            record.get(main_keys[0], "")
        )

    index_values = (
        index_data.split(";")
        if index_data
        else []
    )

    main_values = (
        main_data.split(";")
        if main_data
        else []
    )

    all_values = index_values + main_values

    # --------------------------------------------------
    # Dataset's first 9 fields
    # --------------------------------------------------

    pass_num = (
        _clean(all_values[0])
        if len(all_values) > 0
        else ""
    )

    surname = (
        _clean(all_values[1])
        if len(all_values) > 1
        else ""
    )

    given_name = (
        _clean(all_values[2])
        if len(all_values) > 2
        else ""
    )

    signature = (
        _clean(all_values[3])
        if len(all_values) > 3
        else ""
    )

    date_of_birth = (
        _clean(all_values[4])
        if len(all_values) > 4
        else ""
    )

    date_of_issue = (
        _clean(all_values[5])
        if len(all_values) > 5
        else ""
    )

    date_of_expiry = (
        _clean(all_values[6])
        if len(all_values) > 6
        else ""
    )

    sex = (
        _clean(all_values[7])
        if len(all_values) > 7
        else ""
    )

    place_of_birth = (
        _clean(all_values[8])
        if len(all_values) > 8
        else ""
    )

    # --------------------------------------------------
    # Return normalized record
    # --------------------------------------------------

    return {
        # Dataset metadata
        "pass_num": pass_num,
        "surname": surname,
        "given_name": given_name,
        "signature": signature,
        "date_of_birth": date_of_birth,
        "date_of_issue": date_of_issue,
        "date_of_expiry": date_of_expiry,
        "sex": sex,
        "place_of_birth": place_of_birth,

        # MRZ — authoritative verification data
        "mrz_line1": mrz_line1,
        "mrz_line2": mrz_line2,

        "mrz": (
            f"{mrz_line1}\n{mrz_line2}"
        ),

        "mrz_data": mrz_data,

        # Useful normalized fields directly from MRZ
        "passport_number": mrz_data.get(
            "passport_number"
        ),
        "surname_mrz": mrz_data.get(
            "surname"
        ),
        "given_names_mrz": mrz_data.get(
            "given_names"
        ),
        "nationality_mrz": mrz_data.get(
            "nationality"
        ),
        "date_of_birth_mrz": mrz_data.get(
            "date_of_birth"
        ),
        "sex_mrz": mrz_data.get(
            "sex"
        ),
        "expiry_date_mrz": mrz_data.get(
            "expiry_date"
        ),
    }


def load_normalized_passports():
    """
    Load and normalize all valid passport records.
    """

    dataset = load_passport_dataset()

    passports = []

    for record in dataset:

        try:
            passport = parse_record(record)

            passports.append(passport)

        except (ValueError, TypeError, AttributeError):
            # Ignore malformed records
            continue

    return passports


def find_by_passport_number(
    passport_number,
    passports
):
    """
    Find a passport by passport number.
    """

    if not passport_number:
        return None

    target = (
        str(passport_number)
        .strip()
        .upper()
    )

    for passport in passports:

        dataset_number = passport.get(
            "passport_number",
            ""
        )

        if not dataset_number:
            continue

        if (
            str(dataset_number)
            .strip()
            .upper()
            == target
        ):
            return passport

    return None


def find_by_mrz(
    mrz_line2,
    passports
):
    """
    Find a passport using MRZ line 2.
    """

    if not mrz_line2:
        return None

    target = (
        str(mrz_line2)
        .strip()
        .upper()
    )

    for passport in passports:

        dataset_mrz = passport.get(
            "mrz_line2",
            ""
        )

        if not dataset_mrz:
            continue

        if (
            dataset_mrz
            .strip()
            .upper()
            == target
        ):
            return passport

    return None


def find_passport(
    passport_number=None,
    mrz_line2=None,
    passports=None
):
    """
    Find a passport.

    Search order:
    1. Passport number
    2. MRZ line 2
    """

    if passports is None:
        passports = load_normalized_passports()

    # Passport number lookup
    if passport_number:

        result = find_by_passport_number(
            passport_number,
            passports
        )

        if result:
            return result

    # MRZ lookup
    if mrz_line2:

        result = find_by_mrz(
            mrz_line2,
            passports
        )

        if result:
            return result

    return None