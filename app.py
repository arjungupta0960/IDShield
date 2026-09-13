import io
from datetime import datetime

import streamlit as st

from backend.ocr import extract_text_from_bytes
from backend.document_parser import extract_document_fields
from backend.mrz import (
    find_mrz_lines,
    parse_mrz,
    validate_mrz_structure
)
from backend.validation import (
    validate_mrz,
    validate_document,
    check_expiry
)
from backend.tampering import (
    perform_ela,
    calculate_tampering_score,
    classify_tampering,
    detect_suspicious_regions
)
from backend.duplicate_detection import (
    calculate_image_hash,
    find_duplicate_screening
)
from backend.risk_scoring import calculate_risk_score
from backend.audit import (
    create_audit_record,
    save_audit_record,
    load_audit_records
)
from backend.dataset_manager import load_normalized_passports
from backend.face_verification import compare_faces
from backend.face_photo_detector import detect_document_face
from backend.dashboard import (
    summarize_records,
    record_to_row,
    filter_records,
    export_records_json,
    export_records_csv
)

try:
    from backend.report_generator import generate_screening_report
    REPORTING_AVAILABLE = True
except Exception:
    REPORTING_AVAILABLE = False


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="IDShield — AI Document Screening",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================
# PROFESSIONAL UI
# ============================================================

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 3rem;
        max-width: 1450px;
    }

    .brand {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -0.04em;
        margin-bottom: 0.2rem;
    }

    .subtitle {
        color: #9ca3af;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }

    .eyebrow {
        color: #60a5fa;
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.12em;
    }

    .hero {
        padding: 1.5rem 1.7rem;
        border: 1px solid rgba(148,163,184,.18);
        border-radius: 18px;
        background: linear-gradient(
            135deg,
            rgba(30,41,59,.95),
            rgba(15,23,42,.95)
        );
        margin-bottom: 1.5rem;
    }

    .result-card {
        padding: 1.25rem;
        border-radius: 16px;
        border: 1px solid rgba(148,163,184,.18);
        background: rgba(30,41,59,.55);
        min-height: 125px;
    }

    .result-title {
        color: #94a3b8;
        font-size: .82rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: .06em;
    }

    .result-value {
        font-size: 1.35rem;
        font-weight: 750;
        margin-top: .35rem;
    }

    .muted {
        color: #94a3b8;
    }

    .section-label {
        font-size: 1.45rem;
        font-weight: 750;
        margin-top: .7rem;
        margin-bottom: .8rem;
    }

    div[data-testid="stMetric"] {
        background: rgba(30,41,59,.45);
        border: 1px solid rgba(148,163,184,.15);
        padding: 1rem;
        border-radius: 14px;
    }

    .stButton > button {
        border-radius: 10px;
        font-weight: 700;
    }

    .disclaimer {
        color: #94a3b8;
        font-size: .78rem;
        line-height: 1.5;
        padding: 1rem;
        border: 1px solid rgba(148,163,184,.12);
        border-radius: 12px;
        margin-top: 1.5rem;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:
    st.markdown("## 🛡️ IDShield")
    st.caption("AI Document & Identity Screening")

    page = st.radio(
        "Workspace",
        ["New Screening", "Screening Dashboard"],
        label_visibility="collapsed"
    )

    st.divider()

    st.markdown("### System Status")
    st.success("● OCR Engine")
    st.success("● MRZ Engine")
    st.success("● Risk Engine")
    st.success("● Audit Logging")

    st.divider()

    st.caption("IDShield • Document Screening")


# ============================================================
# COMMON HELPERS
# ============================================================

def status_badge(status):
    mapping = {
        "PASS": ("🟢", "PASS"),
        "FAIL": ("🔴", "FAIL"),
        "REVIEW": ("🟡", "REVIEW"),
        "NEW": ("🟢", "NEW"),
        "DUPLICATE": ("🔴", "DUPLICATE"),
    }
    return mapping.get(status, ("⚪", status or "N/A"))


def render_result_card(title, status, detail=""):
    icon, label = status_badge(status)
    st.markdown(
        f"""
        <div class="result-card">
            <div class="result-title">{title}</div>
            <div class="result-value">{icon} {label}</div>
            <div class="muted">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_risk(level, score):
    if level == "LOW":
        icon = "🟢"
        text = "LIKELY LOW RISK"
    elif level == "MEDIUM":
        icon = "🟡"
        text = "MANUAL REVIEW"
    elif level == "HIGH":
        icon = "🟠"
        text = "SUSPICIOUS"
    else:
        icon = "🔴"
        text = "HIGH RISK"

    st.markdown(
        f"""
        <div class="hero">
            <div class="eyebrow">Overall Risk Assessment</div>
            <div style="font-size:3rem;font-weight:850;">
                {score}<span style="font-size:1.1rem;color:#94a3b8;"> / 100</span>
            </div>
            <div style="font-size:1.35rem;font-weight:750;">
                {icon} {text}
            </div>
            <div class="muted">
                This is an AI-assisted screening signal, not an official
                authenticity or identity determination.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


# ============================================================
# DASHBOARD
# ============================================================

if page == "Screening Dashboard":
    st.markdown('<div class="eyebrow">Operations</div>', unsafe_allow_html=True)
    st.markdown('<div class="brand">Screening Dashboard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Review screening history, risk signals, and audit records.</div>',
        unsafe_allow_html=True
    )

    records = load_audit_records()
    summary = summarize_records(records)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Screenings", summary["total_screenings"])
    c2.metric("Low Risk", summary["low"])
    c3.metric("Medium Risk", summary["medium"])
    c4.metric("High / Critical", summary["high"] + summary["critical"])

    st.divider()

    if not records:
        st.info("No screening records yet. Run a document screening first.")
        st.stop()

    f1, f2 = st.columns([2, 1])

    with f1:
        query = st.text_input(
            "Search",
            placeholder="Screening ID, timestamp, or risk level..."
        )

    with f2:
        risk_filter = st.selectbox(
            "Risk Level",
            ["ALL", "LOW", "MEDIUM", "HIGH", "CRITICAL"]
        )

    filtered = filter_records(records, query, risk_filter)

    st.markdown("### Screening History")

    rows = [record_to_row(record) for record in filtered]

    if rows:
        st.dataframe(
            rows,
            use_container_width=True,
            hide_index=True
        )

        e1, e2 = st.columns(2)
        with e1:
            st.download_button(
                "⬇️ Export CSV",
                data=export_records_csv(filtered),
                file_name="screening_history.csv",
                mime="text/csv"
            )
        with e2:
            st.download_button(
                "⬇️ Export JSON",
                data=export_records_json(filtered),
                file_name="screening_history.json",
                mime="application/json"
            )

        st.divider()

        selected_id = st.selectbox(
            "Open Screening Record",
            [
                record.get("screening_id", "Unknown")
                for record in filtered
            ]
        )

        selected = next(
            (
                record for record in filtered
                if record.get("screening_id") == selected_id
            ),
            None
        )

        if selected:
            risk = selected.get("risk_assessment", {})
            a, b = st.columns(2)
            a.metric("Risk Score", risk.get("score", 0))
            b.metric("Risk Level", risk.get("level", "UNKNOWN"))

            if risk.get("reasons"):
                st.markdown("### Risk Factors")
                for reason in risk["reasons"]:
                    st.write(f"• {reason}")

            with st.expander("View Complete Audit Record"):
                st.json(selected)
    else:
        st.info("No records match the selected filters.")

    st.stop()


# ============================================================
# NEW SCREENING
# ============================================================

st.markdown('<div class="eyebrow">SECURE DOCUMENT SCREENING</div>',
            unsafe_allow_html=True)
st.markdown('<div class="brand">🛡️ IDShield</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">AI-assisted document and identity screening console</div>',
    unsafe_allow_html=True
)

st.markdown(
    """
    <div class="hero">
        <div style="font-size:1.3rem;font-weight:750;">
            Screen a passport or identity document
        </div>
        <div class="muted">
            Upload one document. The system automatically analyzes OCR,
            MRZ integrity, document consistency, image anomalies,
            duplicate history, and the document photograph.
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

st.markdown("### What IDShield Checks")

check_cols = st.columns(7)
checks = [
    ("🔎", "OCR"),
    ("🔐", "MRZ"),
    ("📋", "Consistency"),
    ("🔬", "Image Integrity"),
    ("👤", "Document Photo"),
    ("♻️", "Duplicate"),
    ("⚠️", "Risk"),
]
for col, (icon, label) in zip(check_cols, checks):
    with col:
        st.markdown(
            f"""
            <div class="result-card" style="min-height:90px;text-align:center;padding:.75rem;">
                <div style="font-size:1.25rem;">{icon}</div>
                <div class="result-title" style="margin-top:.3rem;">{label}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

st.markdown("### 📄 Document Input")

uploaded_file = st.file_uploader(
    "Upload passport / identity document",
    type=["jpg", "jpeg", "png"],
    help="Use a clear, high-resolution document image."
)

if not uploaded_file:
    st.info("Upload a document to begin screening.")
    st.markdown(
        """
        <div class="disclaimer">
        🔐 <b>Demo & privacy notice:</b> Use synthetic/test documents for
        demonstrations. The system provides screening signals and does not
        establish legal identity or official document authenticity.
        </div>
        """,
        unsafe_allow_html=True
    )
    st.stop()


image_bytes = uploaded_file.getvalue()

st.success("✓ Document loaded and ready for screening.")

preview_col, input_col = st.columns([1.2, 1])

with preview_col:
    st.markdown("### Document Preview")
    st.image(
        image_bytes,
        caption=uploaded_file.name,
        use_container_width=True
    )

with input_col:
    with st.expander("👤 Optional Identity Verification"):
        st.caption(
            "The document photograph is detected automatically. "
            "Upload a separate reference photograph only if you want "
            "to compare the document holder with an external reference."
        )

        reference_face_file = st.file_uploader(
            "Reference photograph",
            type=["jpg", "jpeg", "png"],
            key="reference_face",
            help="Optional identity-matching input."
        )

        if reference_face_file:
            st.image(
                reference_face_file,
                caption="External Reference",
                width=220
            )

        st.caption(
            "Not required for basic document screening."
        )

st.divider()

analyze = st.button(
    "🔍 Analyze Document",
    type="primary",
    use_container_width=True
)

if not analyze:
    st.stop()


# ============================================================
# ANALYSIS
# ============================================================

with st.spinner("Running document screening pipeline..."):

    try:
        extracted_text = extract_text_from_bytes(image_bytes)
    except Exception as e:
        st.error("OCR analysis failed.")
        st.exception(e)
        st.stop()

    if not extracted_text:
        st.error("No readable text was detected.")
        st.stop()

    mrz_line1, mrz_line2 = find_mrz_lines(extracted_text)

    if not mrz_line1 or not mrz_line2:
        st.error("Machine Readable Zone could not be detected.")
        st.info("Upload a clearer document with the MRZ fully visible.")
        st.stop()

    structure_result = validate_mrz_structure(
        mrz_line1,
        mrz_line2
    )

    if not structure_result["valid"]:
        st.error("MRZ structure is invalid or incomplete.")
        for error in structure_result["errors"]:
            st.write(f"• {error}")
        st.stop()

    try:
        mrz_data = parse_mrz(mrz_line1, mrz_line2)
        validation_results = validate_mrz(mrz_line2)
    except Exception as e:
        st.error("MRZ analysis failed.")
        st.exception(e)
        st.stop()

    document_data = extract_document_fields(extracted_text)

    try:
        consistency_results = validate_document(
            document_data,
            mrz_data
        )
    except Exception as e:
        st.error("Document consistency validation failed.")
        st.exception(e)
        st.stop()

    try:
        expiry_result = check_expiry(
            mrz_data["expiry_date"]
        )
    except Exception as e:
        st.error("Expiry validation failed.")
        st.exception(e)
        st.stop()

    # Image Integrity
    try:
        ela_image, mean_error, max_error = perform_ela(image_bytes)
        tampering_score = calculate_tampering_score(
            mean_error,
            max_error
        )
        tampering_result = classify_tampering(tampering_score)
        annotated_ela, suspicious_regions, _ = detect_suspicious_regions(
            ela_image
        )
    except Exception as e:
        tampering_result = {
            "status": "REVIEW",
            "label": "ANALYSIS UNAVAILABLE",
            "message": "Image Integrity analysis was unavailable."
        }
        tampering_score = 0
        mean_error = 0
        max_error = 0
        suspicious_regions = []
        annotated_ela = None

    # Automatic document-photo detection
    try:
        document_face = detect_document_face(image_bytes)
    except Exception:
        document_face = {
            "detected": False,
            "count": 0,
            "location": None,
            "face_image": None
        }

    # Optional identity comparison
    face_result = None

    if reference_face_file and document_face["detected"]:
        try:
            face_result = compare_faces(
                reference_face_file.getvalue(),
                document_face["face_image"]
            )
        except Exception:
            face_result = {
                "status": "REVIEW",
                "score": 0.0,
                "message": "Identity comparison was unavailable."
            }

    # Dataset
    dataset_match_result = {
        "status": "REVIEW",
        "matched": False,
        "message": "Dataset verification unavailable."
    }

    try:
        passport_records = load_normalized_passports()
        target_number = (
            mrz_data.get("passport_number", "").strip().upper()
        )

        dataset_match = next(
            (
                record for record in passport_records
                if record.get("passport_number", "").strip().upper()
                == target_number
            ),
            None
        )

        if dataset_match is None:
            target_mrz = mrz_line2.strip().upper()
            dataset_match = next(
                (
                    record for record in passport_records
                    if record.get("mrz_line2", "").strip().upper()
                    == target_mrz
                ),
                None
            )

        if dataset_match:
            dataset_match_result = {
                "status": "PASS",
                "matched": True,
                "message": "Passport matched a synthetic dataset record.",
                "matched_passport_number": dataset_match.get("passport_number"),
                "matched_surname": dataset_match.get("surname_mrz"),
                "matched_given_names": dataset_match.get("given_names_mrz"),
                "matched_nationality": dataset_match.get("nationality_mrz"),
                "matched_sex": dataset_match.get("sex_mrz"),
                "matched_expiry": dataset_match.get("expiry_date_mrz")
            }
        else:
            dataset_match_result = {
                "status": "REVIEW",
                "matched": False,
                "message": "No matching synthetic dataset record was found.",
                "dataset_records_available": len(passport_records)
            }
    except Exception as e:
        dataset_match_result["error"] = str(e)

    # Duplicate
    try:
        duplicate_result = find_duplicate_screening(
            image_bytes,
            load_audit_records()
        )
    except Exception:
        duplicate_result = {
            "matched": False,
            "status": "UNAVAILABLE",
            "distance": None,
            "screening_id": None,
            "message": "Duplicate detection unavailable."
        }

    # Risk
    risk_result = calculate_risk_score(
        mrz_checks=validation_results,
        consistency_results=consistency_results,
        expiry_result=expiry_result,
        tampering_result=tampering_result,
        face_result=face_result
    )

    # Duplicate detection is an independent screening signal. Keep it outside
    # the risk_scoring module so older compatible versions of that module work.
    if duplicate_result.get("matched", False):
        risk_result["score"] = min(risk_result["score"] + 20, 100)
        risk_result["reasons"].append(
            "Similar document image was previously screened."
        )

    # Dataset is a supporting signal, not proof of fraud.
    if dataset_match_result.get("matched") is False:
        risk_result["score"] = min(
            risk_result["score"] + 8,
            100
        )
        risk_result["reasons"].append(
            "No matching synthetic dataset record found."
        )

    if risk_result["score"] < 20:
        risk_result["level"] = "LOW"
    elif risk_result["score"] < 50:
        risk_result["level"] = "MEDIUM"
    elif risk_result["score"] < 75:
        risk_result["level"] = "HIGH"
    else:
        risk_result["level"] = "CRITICAL"


# ============================================================
# SCREENING SUMMARY
# ============================================================

st.divider()
st.markdown("### 🎯 Screening Summary")

s1, s2, s3, s4, s5 = st.columns(5)

with s1:
    render_result_card(
        "OCR",
        "PASS",
        f"{len(extracted_text)} text lines"
    )

with s2:
    render_result_card(
        "MRZ Integrity",
        "PASS" if all(validation_results.values()) else "FAIL",
        "5 check-digit tests"
    )

with s3:
    render_result_card(
        "Consistency",
        "FAIL" if any(v is False for v in consistency_results.values())
        else ("REVIEW" if any(v is None for v in consistency_results.values())
              else "PASS"),
        "Visible fields vs MRZ"
    )

with s4:
    render_result_card(
        "Image Integrity",
        tampering_result.get("status", "REVIEW"),
        f"Score {tampering_score}/100"
    )

with s5:
    render_result_card(
        "Duplicate",
        duplicate_result.get("status", "REVIEW"),
        duplicate_result.get("message", "")
    )


# ============================================================
# RISK
# ============================================================

render_risk(
    risk_result["level"],
    risk_result["score"]
)

if risk_result["reasons"]:
    with st.expander("⚠️ View Risk Factors", expanded=True):
        for reason in risk_result["reasons"]:
            st.write(f"• {reason}")


# ============================================================
# DOCUMENT PHOTO + IDENTITY
# ============================================================

st.divider()
st.markdown("### 👤 Document Photograph & Identity Verification")

p1, p2 = st.columns([1, 1.5])

with p1:
    if document_face["detected"]:
        st.success(
            f"🟢 Passport photograph detected "
            f"({document_face['count']} face candidate)"
        )
        st.image(
            document_face["face_image"],
            caption="Automatically detected document photograph",
            width=260
        )
    else:
        st.warning(
            "🟡 No confident face detected in the document image."
        )
        st.caption(
            "This does not prove that the document is fake. "
            "The photo may be too small, blurred, or outside the detector's range."
        )

with p2:
    if reference_face_file:
        if document_face["detected"]:
            if face_result:
                face_status = face_result.get("status", "REVIEW")
                render_result_card(
                    "Identity Match",
                    face_status,
                    face_result.get("message", "")
                )
                st.metric(
                    "Similarity",
                    f'{face_result.get("score", 0)}/100'
                )
                if face_result.get("distance") is not None:
                    st.caption(
                        f"Face distance: {face_result['distance']:.4f}"
                    )
            else:
                st.warning("Identity comparison was unavailable.")
        else:
            st.info(
                "A reference photo was supplied, but there is no confident "
                "document face to compare against."
            )
    else:
        st.info(
            "Identity matching was not requested. "
            "Basic document screening does not require a second photo."
        )


# ============================================================
# TECHNICAL DETAILS
# ============================================================

st.divider()

with st.expander("🔎 OCR & Structured Fields"):
    st.markdown("#### Raw OCR")
    st.code("\n".join(extracted_text))

    st.markdown("#### Structured Visible Fields")
    field_labels = {
        "passport_number": "Passport Number",
        "surname": "Surname",
        "given_names": "Given Names",
        "nationality": "Nationality",
        "date_of_birth": "Date of Birth",
        "sex": "Sex",
        "date_of_issue": "Date of Issue",
        "date_of_expiry": "Date of Expiry",
        "place_of_birth": "Place of Birth",
        "place_of_issue": "Place of Issue"
    }

    st.dataframe(
        [
            {
                "Field": label,
                "OCR Value": document_data.get(key) or "Not detected"
            }
            for key, label in field_labels.items()
        ],
        use_container_width=True,
        hide_index=True
    )

with st.expander("🔐 MRZ Details"):
    st.code(f"{mrz_line1}\n{mrz_line2}")
    st.json(mrz_data)

with st.expander("📋 Consistency Results"):
    st.json(consistency_results)

with st.expander("🔬 Image Integrity Analysis"):
    t1, t2, t3 = st.columns(3)
    t1.metric("Image Integrity Score", f"{tampering_score}/100")
    t2.metric("Mean Error", f"{mean_error:.2f}")
    t3.metric("Maximum Error", str(max_error))

    if suspicious_regions:
        st.warning(
            f"{len(suspicious_regions)} localized anomaly candidate(s) detected."
        )
        st.image(
            annotated_ela,
            caption="Localized ELA anomaly candidates"
        )
        st.caption(
            "ELA anomalies are forensic screening signals, not proof of manipulation."
        )
    else:
        st.success("No strong localized anomaly region detected.")

with st.expander("🗂️ Reference Dataset Check"):
    if dataset_match_result.get("matched"):
        st.success(dataset_match_result["message"])
        st.json(dataset_match_result)
    else:
        st.warning(dataset_match_result["message"])
        st.caption(
            "The synthetic reference dataset is a supporting signal only."
        )

with st.expander("♻️ Duplicate Detection"):
    st.json(duplicate_result)


# ============================================================
# AUDIT
# ============================================================

st.divider()
st.markdown("### 🧾 Audit & Reporting")

try:
    audit_record = create_audit_record(
        mrz_checks=validation_results,
        consistency_results=consistency_results,
        expiry_result=expiry_result,
        tampering_result=tampering_result,
        risk_result=risk_result
    )

    audit_record["document_fingerprint"] = calculate_image_hash(
        image_bytes
    )

    audit_record["duplicate_detection"] = {
        "status": duplicate_result.get("status"),
        "matched": duplicate_result.get("matched"),
        "distance": duplicate_result.get("distance"),
        "previous_screening_id": duplicate_result.get("screening_id"),
        "message": duplicate_result.get("message")
    }

    audit_record["document_photo_detection"] = {
        "detected": document_face["detected"],
        "face_count": document_face["count"]
    }

    if face_result is not None:
        audit_record["face_verification"] = {
            "status": face_result.get("status"),
            "score": face_result.get("score"),
            "distance": face_result.get("distance"),
            "message": face_result.get("message")
        }

    audit_file = save_audit_record(audit_record)

    st.success(
        f"Screening saved • {audit_record['screening_id']}"
    )

    a1, a2 = st.columns([1, 1])

    with a1:
        with st.expander("View Audit Record"):
            st.json(audit_record)

    with a2:
        if REPORTING_AVAILABLE:
            try:
                pdf = generate_screening_report(audit_record)
                st.download_button(
                    "📄 Download Screening Report",
                    data=pdf,
                    file_name=(
                        f"{audit_record['screening_id']}_report.pdf"
                    ),
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.warning("PDF report generation unavailable.")
                st.caption(str(e))

    st.caption(f"Local audit file: {audit_file}")

except Exception as e:
    st.error("Audit record could not be saved.")
    st.exception(e)


# ============================================================
# FINAL DECISION
# ============================================================

st.divider()
st.markdown("### 🚨 Final Screening Decision")

if (
    any(v is False for v in validation_results.values())
    or any(v is False for v in consistency_results.values())
    or expiry_result.get("valid") is False
    or tampering_result.get("status") == "FAIL"
    or (
        face_result is not None
        and face_result.get("status") == "FAIL"
    )
    or risk_result["level"] in ["HIGH", "CRITICAL"]
):
    st.error(
        "🔴 HIGH-RISK SIGNALS — MANUAL REVIEW REQUIRED"
    )
elif (
    any(v is None for v in consistency_results.values())
    or tampering_result.get("status") == "REVIEW"
    or (
        face_result is not None
        and face_result.get("status") == "REVIEW"
    )
    or risk_result["level"] == "MEDIUM"
):
    st.warning(
        "🟡 REVIEW REQUIRED"
    )
else:
    st.success(
        "🟢 LOW RISK — INITIAL SCREENING PASSED"
    )

st.markdown(
    """
    <div class="disclaimer">
    <b>Prototype limitation:</b> This application combines OCR, MRZ
    validation, image-forensics heuristics, face comparison, duplicate
    screening, and reference-data signals. These methods can produce
    false positives and false negatives. The result must not be treated
    as an official determination of identity, passport authenticity,
    citizenship, or legal validity.
    </div>
    """,
    unsafe_allow_html=True
)
