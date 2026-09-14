# 🛡️ IDShield — AI Document & Identity Screening

IDShield is an AI-assisted document screening prototype that combines multiple verification signals to assess whether an uploaded identity document should be passed, reviewed, or flagged for further investigation.

The system is designed as a multi-stage screening pipeline rather than relying on a single detection technique.

> **Prototype disclaimer:** IDShield is not an official identity-verification or document-authentication system. Its results are screening signals and can contain false positives or false negatives. Demonstrations should use synthetic or authorized test documents.

---

## 🚀 Live Demo

**[Launch IDShield](https://idshield.streamlit.app/)**

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

## 🧠 Screening pipeline

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

## 🎯 Why a multi-signal approach?

IDShield does not treat one signal as definitive proof of fraud.

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

## ⚙️ Tech stack

### Application

- Python
- Streamlit

### OCR & document processing

- PaddleOCR
- Pillow
- OpenCV
- NumPy

### Identity verification

- **OpenCV YuNet** — face detection
- **OpenCV SFace** — face feature extraction and similarity matching

### Data & reference checks

- Hugging Face Datasets
- Synthetic passport reference data

### Image forensics

- Error Level Analysis (ELA)
- Localized suspicious-region analysis

### Reporting

- ReportLab

### Version control & deployment

- Git
- GitHub
- Streamlit Cloud

---

## 📁 Project structure

```text
IDShield/
│
├── app.py
├── requirements.txt
├── packages.txt
├── README.md
├── UI_DESIGN.md
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
├── models/
│   ├── face_detection_yunet_2023mar.onnx
│   └── face_recognition_sface_2021dec.onnx
│
├── data/
│   └── synthetic / authorized test data
│
├── audit_logs/
│   └── local screening records
│
├── test_face_verification.py
├── generate_test_passport.py
└── create_tampered_passport.py
```

> Local runtime files such as the virtual environment, audit JSON files, private documents, and other sensitive test data should not be committed to a public repository.

---

## 🛠️ Running locally

### 1. Clone the repository

```powershell
git clone https://github.com/arjungupta0960/IDShield.git
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

## 🧪 Typical demo workflow

1. Open **New Screening**.
2. Upload a synthetic or authorized test document.
3. Start document analysis.
4. Review the screening summary.
5. Inspect the risk level and contributing factors.
6. Review document photograph detection.
7. Optionally provide a reference photograph for face similarity verification.
8. Open advanced analysis to inspect OCR, MRZ, consistency, and image-integrity results.
9. Review the audit record.
10. Generate or inspect the screening report.
11. Open **Screening Dashboard** to review screening history and exports.

---

## 🔬 Testing strategy

IDShield can be evaluated using synthetic or authorized labelled documents.

Recommended test categories:

### Genuine / Bona-fide documents

Test whether legitimate-looking documents produce appropriately low-risk results.

### Forged / Tampered documents

Test whether manipulated documents generate stronger warning signals.

### Face verification

```text
Same face       → PASS
Different face  → FAIL
Unclear case    → REVIEW
```

### MRZ testing

Test:

- valid MRZ
- invalid check digits
- incorrect passport number
- incorrect dates
- visible-field / MRZ inconsistencies

For meaningful evaluation, results should be recorded against known ground-truth labels rather than relying on a single demonstration.

---

## 📊 Risk assessment

The risk score is a prototype decision-support mechanism.

Signals may include:

```text
MRZ validation
      +
Document consistency
      +
Expiry status
      +
Image integrity
      +
Face similarity
      +
Duplicate detection
      +
Reference dataset
      │
      ▼
  Risk Score
      │
      ▼
LOW / MEDIUM / HIGH / CRITICAL
```

The system is designed to provide **explainable supporting factors** alongside the risk level.

It does not claim that a risk score represents a statistically validated probability of fraud.

---

## 🔐 Privacy and security

IDShield is intended for synthetic or authorized testing.

**Do not upload real passports, government IDs, or private biometric photographs to this public repository.**

Before using a system like this with real identity information, additional controls would be required, including:

- authentication and authorization
- secure storage
- encryption
- controlled access to biometric information
- retention and deletion policies
- secure secret management
- audit and monitoring controls
- appropriate legal and privacy review

Audit records are intended to contain screening metadata and analysis results rather than the uploaded passport image itself.

---

## ⚠️ Limitations

IDShield is a prototype and has important limitations.

### OCR

OCR accuracy depends on image quality, document layout, lighting, blur, and text orientation.

### MRZ

MRZ validation checks structure and mathematical check-digit consistency. A mathematically valid MRZ does **not** prove that a passport is genuine.

### Image integrity

ELA and localized image-error detection are heuristic signals. Compression history and normal image processing can create similar patterns.

### Face verification

Face similarity is sensitive to image quality, cropping, lighting, pose, and reference-image quality. It indicates similarity between images and should not be treated as definitive identity proof.

### Duplicate detection

Duplicate screening is based on image similarity and local screening history. It is not a global identity or document database.

### Reference dataset

The reference dataset is synthetic and limited. A missing dataset match is not proof that a document is fraudulent.

### Risk score

The risk score is a prototype decision-support mechanism. It should not be interpreted as a statistically validated probability of fraud.

---

## 📚 Datasets and references

### Synthetic Indian Passport Dataset

Synthetic passport data used for development and testing of the OCR, document parsing, and MRZ workflow.

**Dataset:**  
https://huggingface.co/datasets/ud-synthetic/indian-passports

### SIDTD — Synthetic Dataset of ID and Travel Documents

A research dataset containing bona-fide and forged identity/travel document samples for document-forensics research.

**Dataset:**  
https://tc11.cvc.uab.es/datasets/SIDTD_1

### OpenCV Zoo

OpenCV Zoo provides the YuNet and SFace models used by IDShield for face detection and face similarity verification.

**Repository:**  
https://github.com/opencv/opencv_zoo

---

## 🚀 Deployment

IDShield is deployed using Streamlit Cloud.

### Live application

**https://idshield.streamlit.app/**

The deployed application uses:

- Streamlit
- PaddleOCR / PaddlePaddle
- OpenCV YuNet
- OpenCV SFace
- ONNX face models
- Synthetic reference data
- ReportLab

---

## 🔮 Future improvements

Potential next steps include:

- [ ] Larger and better-labelled document datasets
- [ ] Quantitative evaluation across genuine and tampered samples
- [ ] Confusion matrix, precision, recall, and F1 evaluation
- [ ] Stronger document-layout analysis
- [ ] Learned image-forensics models
- [ ] Improved face-verification evaluation
- [ ] Database-backed duplicate detection
- [ ] Authenticated multi-user access
- [ ] Secure production deployment
- [ ] Model/version tracking
- [ ] Automated evaluation and regression tests

---

## 🎓 Project context

IDShield was developed as a hands-on machine-learning and computer-vision project exploring document screening, OCR, image forensics, and identity-similarity analysis.

The project focuses on combining multiple independent signals instead of relying on a single AI prediction.

---

## 👨‍💻 Author

**Arjun Gupta**

BTech — Computer Science & Engineering

GitHub:  
https://github.com/arjungupta0960

LinkedIn:  
https://www.linkedin.com/in/arjun-gupta-87a34737a/

---

## ⭐ Project

If you find IDShield useful or interesting, consider giving the repository a ⭐ on GitHub.

### Live Demo

**https://idshield.streamlit.app/**
