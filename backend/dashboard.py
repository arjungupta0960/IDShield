import json
import os
from datetime import datetime
from pathlib import Path


def summarize_records(records):
    total = len(records)
    levels = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}

    for record in records:
        level = (
            record.get("risk_assessment", {})
            .get("level", "UNKNOWN")
        )
        if level in levels:
            levels[level] += 1

    return {
        "total_screenings": total,
        "low": levels["LOW"],
        "medium": levels["MEDIUM"],
        "high": levels["HIGH"],
        "critical": levels["CRITICAL"],
    }


def record_to_row(record):
    risk = record.get("risk_assessment", {})
    tampering = record.get("tampering_detection", {})
    face = record.get("face_verification", {})
    duplicate = record.get("duplicate_detection", {})

    return {
        "Screening ID": record.get("screening_id", "N/A"),
        "Timestamp": record.get("timestamp", "N/A"),
        "Risk Score": risk.get("score", 0),
        "Risk Level": risk.get("level", "UNKNOWN"),
        "Tampering": tampering.get("status", "N/A"),
        "Face": face.get("status", "N/A"),
        "Duplicate": (
            "YES" if duplicate.get("matched") else "NO"
        ),
    }


def filter_records(records, query="", risk_level="ALL"):
    query = (query or "").strip().lower()

    filtered = []

    for record in records:
        level = (
            record.get("risk_assessment", {})
            .get("level", "UNKNOWN")
        )

        if risk_level != "ALL" and level != risk_level:
            continue

        searchable = " ".join([
            str(record.get("screening_id", "")),
            str(record.get("timestamp", "")),
            str(level),
        ]).lower()

        if query and query not in searchable:
            continue

        filtered.append(record)

    return filtered


def export_records_json(records):
    return json.dumps(
        records,
        indent=4,
        ensure_ascii=False
    ).encode("utf-8")


def export_records_csv(records):
    import csv
    import io

    output = io.StringIO()
    rows = [record_to_row(record) for record in records]

    if not rows:
        return b""

    writer = csv.DictWriter(
        output,
        fieldnames=list(rows[0].keys())
    )
    writer.writeheader()
    writer.writerows(rows)

    return output.getvalue().encode("utf-8")
