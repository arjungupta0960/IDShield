# IDShield — AI Document & Identity Screening

IDShield is an AI-assisted document screening prototype that combines multiple verification signals to assess whether an uploaded identity document should be passed, reviewed, or flagged for further investigation.

The system is designed as a multi-stage screening pipeline rather than relying on a single detection technique.

> **Prototype disclaimer:** IDShield is not an official identity-verification or document-authentication system. Its results are screening signals and can contain false positives or false negatives. Demonstrations should use synthetic or authorized test documents.

---

## What it checks

IDShield currently combines:

- **OCR** — extracts text from the uploaded document.
- **MRZ analysis** — detects and parses passport MRZ data.
- **MRZ integrity** — validates ICAO-style check digits.
- **Document consistency** — compares visible document fields with MRZ-derived fields.
- **Expiry validation** — checks document expiry information.
- **Image integrity analysis** — uses Error Level Analysis (ELA) as an image-forensics screening signal.
- **Suspicious-region detection** — identifies localized high-error image regions for review.
- **Document photograph detection** — automatically looks for a face/photo region on the document.
- **Optional identity verification** — compares the detected document photograph with a separately supplied reference photograph.
- **Duplicate screening** — compares the uploaded document against previous local screening records.
- **Reference dataset check** — compares supported passport information against a synthetic reference dataset.
- **Risk scoring** — combines the available signals into an explainable risk assessment.
- **Audit trail** — stores screening results locally with a unique screening ID.
- **Dashboard & reporting** — provides screening history, exports, and PDF reports.

---

## Screening pipeline

```text
                    Uploaded Document
                           │
                           ▼
                         OCR
                           │
                           ▼
                    Document Parsing
                           │
             ┌─────────────┴─────────────┐
             ▼                           ▼
        Visible Fields                  MRZ
             │                           │
             │                     MRZ Validation
             │                           │
             └─────────────┬─────────────┘
                           ▼
                 Consistency Checking
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
     Expiry Check     Image Integrity   Photo Detection
                           │                │
                           │                ▼
                           │       Optional Face Verification
                           │
          ┌────────────────┴────────────────┐
          ▼                                 ▼
 Reference Dataset                    Duplicate Screening
          │                                 │
          └────────────────┬────────────────┘
                           ▼
                     Risk Scoring
                           │
                           ▼
                Screening Decision
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
          Audit Record             PDF Report
```

---

## Risk assessment

The application does not treat one signal as definitive proof of fraud.

Instead, different checks contribute to an overall screening assessment. Examples include:

- failed MRZ check digits
- visible-field / MRZ inconsistencies
- image-integrity anomalies
- expired documents
- failed or inconclusive face comparison
- duplicate-document matches
- reference-dataset mismatch

The resulting assessment is presented as a risk level and supporting risk factors so that the result can be reviewed rather than treated as an automatic legal determination.

---

## Tech stack

### Application

- Python
- Streamlit

### OCR & document processing

- PaddleOCR
- Pillow
- OpenCV
- NumPy

### Identity verification

- `face-recognition`
- dlib

### Data & reference checks

- Hugging Face Datasets
- Synthetic passport reference data

### Reporting

- ReportLab

### Version control

- Git / GitHub

---

## Project structure

```text
IDShield/
│
├── app.py
│
├── backend/
│   ├── ocr.py
│   ├── mrz.py
│   ├── validation.py
│   ├── tampering.py
│   ├── face_verification.py
│   ├── face_photo_detector.py
│   ├── duplicate_detection.py
│   ├── risk_scoring.py
│   ├── audit.py
│   ├── dataset_manager.py
│   ├── document_parser.py
│   ├── dashboard.py
│   └── report_generator.py
│
├── test_face_verification.py
├── generate_test_passport.py
├── create_tampered_passport.py
│
├── README.md
├── UI_DESIGN.md
├── requirements.txt
└── .gitignore
```

Local runtime files such as the virtual environment, audit JSON files, and private/test data should not be committed to a public repository.

---

## Running locally

### 1. Clone the repository

```powershell
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd IDShield
```

### 2. Create a virtual environment

```powershell
python -m venv venv
```

### 3. Activate it

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

### 5. Start the application

```powershell
python -m streamlit run app.py
```

The Streamlit application will provide the local address in the terminal.

---

## Typical demo workflow

1. Open **New Screening**.
2. Upload a synthetic/test document.
3. Start document analysis.
4. Review the screening summary.
5. Inspect the risk level and contributing factors.
6. Review document photograph detection.
7. Optionally provide a reference photograph for identity comparison.
8. Open advanced analysis to inspect OCR, MRZ, consistency, and image-integrity results.
9. Review the audit record.
10. Generate or inspect the screening report.

---

## Testing and synthetic documents

The repository includes utilities for creating controlled test documents and a face-verification test script.

These are intended for development and demonstration rather than representing real identity documents.

For a public repository, only synthetic or explicitly authorized assets should be included.

---

## Limitations

IDShield is a prototype and has important limitations.

### OCR

OCR accuracy depends on image quality, document layout, lighting, blur, and text orientation.

### MRZ

The MRZ validation checks structural and check-digit consistency. A mathematically valid MRZ does **not** prove that a passport is genuine.

### Image integrity

ELA and localized image-error detection are heuristic signals. Compression history and normal image processing can create similar patterns.

### Face verification

Face comparison is sensitive to image quality, cropping, lighting, pose, and the quality of the reference photograph. It should not be treated as definitive identity proof.

### Duplicate detection

Duplicate screening is based on image similarity and local screening history. It is not a global identity or document database.

### Reference dataset

The reference dataset is synthetic and limited. A missing dataset match is not proof that a document is fraudulent.

### Risk score

The risk score is a prototype decision-support mechanism. It should not be interpreted as a statistically validated probability of fraud.

---

## Privacy and security

Do not upload real passports, government IDs, or private biometric photographs to a public GitHub repository.

Before using a system like this with real identity information, additional controls would be required, including:

- authentication and authorization
- secure storage
- encryption
- controlled access to biometric information
- retention and deletion policies
- secure secret management
- audit and monitoring controls
- appropriate legal and privacy review

---

## Future improvements

Potential next steps include:

- larger and better-labeled document datasets
- quantitative evaluation across genuine and tampered samples
- stronger document-layout analysis
- learned image-forensics models
- improved face verification evaluation
- database-backed duplicate detection
- authenticated multi-user access
- secure deployment
- model/version tracking
- automated evaluation and regression tests

---

## Author

**Arjun Gupta**

BTech Computer Science & Engineering

This project was developed as a hands-on machine-learning/document-screening portfolio project.
