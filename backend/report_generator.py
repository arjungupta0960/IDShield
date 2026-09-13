from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)


def _status_text(value):
    if value is True:
        return "PASS"
    if value is False:
        return "FAIL"
    return "REVIEW"


def generate_screening_report(record):
    """
    Generate a downloadable PDF screening report from an audit record.
    No document image is embedded in the report.
    """
    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="AI Document Screening Report",
        author="SIH26188",
    )

    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        spaceAfter=8,
    )
    heading = ParagraphStyle(
        "ReportHeading",
        parent=styles["Heading2"],
        fontSize=13,
        leading=16,
        spaceBefore=10,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=13,
    )
    small = ParagraphStyle(
        "ReportSmall",
        parent=styles["BodyText"],
        fontSize=7.5,
        leading=10,
        textColor=colors.grey,
    )

    story = []

    story.append(
        Paragraph(
            "AI-Based Fake Identity & Document Screening",
            title,
        )
    )
    story.append(
        Paragraph(
            "Smart India Hackathon 2026 — SIH26188",
            body,
        )
    )
    story.append(Spacer(1, 6))

    story.append(Paragraph("Screening Information", heading))
    info = [
        ["Screening ID", str(record.get("screening_id", "N/A"))],
        ["Timestamp", str(record.get("timestamp", "N/A"))],
    ]
    story.append(_table(info))

    risk = record.get("risk_assessment", {})
    story.append(Paragraph("Risk Assessment", heading))
    story.append(
        _table([
            ["Risk Score", f'{risk.get("score", 0)}/100'],
            ["Risk Level", str(risk.get("level", "UNKNOWN"))],
        ])
    )

    story.append(Paragraph("Verification Results", heading))

    mrz = record.get("mrz_validation", {})
    verification_rows = [
        ["Passport Number Check", _status_text(mrz.get("passport_number"))],
        ["Date of Birth Check", _status_text(mrz.get("date_of_birth"))],
        ["Expiry Date Check", _status_text(mrz.get("expiry_date"))],
        ["Optional Data Check", _status_text(mrz.get("optional_data"))],
        ["Composite Check", _status_text(mrz.get("composite"))],
    ]

    consistency = record.get("document_consistency", {})
    for field, value in consistency.items():
        verification_rows.append(
            [f"Consistency — {field}", _status_text(value)]
        )

    expiry = record.get("expiry_check", {})
    verification_rows.append(
        ["Document Expiry", "VALID" if expiry.get("valid") else "INVALID"]
    )

    tampering = record.get("tampering_detection", {})
    verification_rows.append(
        ["Tampering Screening", str(tampering.get("status", "N/A"))]
    )

    face = record.get("face_verification", {})
    if face:
        verification_rows.append(
            ["Face Verification", str(face.get("status", "N/A"))]
        )

    duplicate = record.get("duplicate_detection", {})
    if duplicate:
        verification_rows.append(
            [
                "Duplicate Detection",
                "DUPLICATE" if duplicate.get("matched") else "NEW"
            ]
        )

    story.append(_table(verification_rows))

    reasons = risk.get("reasons", [])
    story.append(Paragraph("Risk Factors", heading))

    if reasons:
        for reason in reasons:
            story.append(
                Paragraph(f"• {reason}", body)
            )
    else:
        story.append(
            Paragraph(
                "No risk factors were recorded.",
                body
            )
        )

    story.append(Paragraph("Final Assessment", heading))

    level = str(risk.get("level", "UNKNOWN"))
    if level == "LOW":
        assessment = "LIKELY LOW RISK — No major screening concern was recorded."
    elif level == "MEDIUM":
        assessment = "MANUAL REVIEW — Some screening signals require human review."
    elif level == "HIGH":
        assessment = "SUSPICIOUS — Multiple elevated-risk signals were detected."
    elif level == "CRITICAL":
        assessment = "HIGH RISK — Strong risk signals were detected."
    else:
        assessment = "REVIEW — Screening result requires interpretation."

    story.append(Paragraph(assessment, body))
    story.append(Spacer(1, 12))

    story.append(
        Paragraph(
            "Important: This report is an AI-assisted screening result for a "
            "prototype system. It is not proof of document authenticity, "
            "identity, or legal validity. Final decisions should be made by "
            "an authorized human reviewer using appropriate official sources.",
            small,
        )
    )

    doc.build(story)
    return buffer.getvalue()


def _table(rows):
    table = Table(
        rows,
        colWidths=[72 * mm, 100 * mm],
        repeatRows=0,
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAF2F8")),
            ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#B8C4CE")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ])
    )

    return table
