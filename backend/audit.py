import json
import os
from datetime import datetime


AUDIT_DIRECTORY = "audit_logs"


def generate_screening_id():
    """
    Generate a unique screening ID.
    """

    timestamp = datetime.now().strftime(
        "%Y%m%d-%H%M%S-%f"
    )

    return f"DOC-{timestamp}"


def create_audit_record(
    mrz_checks,
    consistency_results,
    expiry_result,
    tampering_result,
    risk_result
):
    """
    Create a structured audit record for
    a document screening operation.
    """

    screening_id = generate_screening_id()

    timestamp = datetime.now().isoformat(
        timespec="seconds"
    )

    record = {
        "screening_id": screening_id,
        "timestamp": timestamp,

        "mrz_validation": mrz_checks,

        "document_consistency": consistency_results,

        "expiry_check": {
            "valid": expiry_result.get("valid"),
            "message": expiry_result.get("message")
        },

        "tampering_detection": {
            "status": tampering_result.get("status"),
            "label": tampering_result.get("label"),
            "message": tampering_result.get("message")
        },

        "risk_assessment": {
            "score": risk_result.get("score"),
            "level": risk_result.get("level"),
            "reasons": risk_result.get("reasons", [])
        }
    }

    return record


def save_audit_record(record):
    """
    Save an audit record as a JSON file.
    """

    os.makedirs(
        AUDIT_DIRECTORY,
        exist_ok=True
    )

    screening_id = record["screening_id"]

    file_path = os.path.join(
        AUDIT_DIRECTORY,
        f"{screening_id}.json"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            record,
            file,
            indent=4,
            ensure_ascii=False
        )

    return file_path


def load_audit_records():
    """
    Load all previously saved audit records.
    """

    if not os.path.exists(AUDIT_DIRECTORY):
        return []

    records = []

    for filename in os.listdir(AUDIT_DIRECTORY):

        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(
            AUDIT_DIRECTORY,
            filename
        )

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8"
            ) as file:

                record = json.load(file)

                records.append(record)

        except (
            json.JSONDecodeError,
            OSError
        ):

            continue

    # Newest records first
    records.sort(
        key=lambda x: x.get(
            "timestamp",
            ""
        ),
        reverse=True
    )

    return records