# Medify — Medical Report AI

Medify is an AI-powered medical report explanation platform that helps users turn supported medical-report images into structured, easier-to-understand information.

## What Medify Does

Medify follows a multi-stage analysis pipeline:

1. **Extract** — reads visible information from the uploaded report.
2. **Verify** — checks extracted values, units, and reference ranges against the original report image.
3. **Interpret** — explains verified laboratory results in simple language.
4. **Present** — displays the results in a structured web interface with light/dark mode.

The system is designed for **educational explanation**, not diagnosis or treatment.

## Key Features

- Upload supported medical-report images
- AI-based report extraction
- Verification against the original report image
- Reference-range comparison
- User-friendly result status messages
- Simple explanations for laboratory tests
- Patient age and sex extraction when explicitly visible
- Light and dark themes
- Animated analysis stages
- Smooth Analysis → Results transition
- Responsive Results dashboard
- FastAPI backend
- Vercel frontend
- Render backend deployment

## Supported Files

The current version accepts:

- JPG / JPEG
- PNG
- WEBP

Maximum upload size: **10 MB**

## Technology Stack

### Frontend
- HTML
- CSS
- JavaScript
- Vercel

### Backend
- Python
- FastAPI
- Pydantic
- Google Gemini API
- Render

## Project Structure

```text
medical-report-ai/
├── .env
├── .gitignore
├── analyze_report.py
├── extract_report.py
├── interpret_report.py
├── main.py
├── medical_ai.py
├── requirements.txt
├── test_gemini.py
├── test_image.py
├── user_context.json
├── verified_report.json
├── images/
└── frontend/
    ├── index.html
    ├── upload.html
    ├── results.html
    ├── app.js
    ├── style.css
    └── assets/
        └── medify-logo.png
```

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/student-g25/medical-report-ai.git
cd medical-report-ai
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the Gemini API key

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_api_key_here
```

Never commit `.env` or expose the API key in frontend code.

### 5. Run the backend

```bash
uvicorn main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

FastAPI documentation:

```text
http://127.0.0.1:8000/docs
```

### 6. Run the frontend

The frontend is contained in the `frontend/` directory. It can be served with a local static-file server or deployed through Vercel.

## API

### POST `/analyze-report`

Accepts a supported medical-report image and returns a structured analysis.

The response contains information such as:

- patient information
- verified report data
- interpretation summary
- individual test results
- reference ranges
- status
- user-friendly status
- simple explanations
- important points
- doctor discussion questions
- limitations

## Safety & Limitations

Medify is intended to explain information already present in a medical report.

The analysis pipeline is designed to:

- avoid changing reported values
- preserve reported units
- preserve the report's supplied reference ranges
- avoid inventing missing information
- avoid diagnosing diseases
- avoid recommending medication
- avoid providing treatment instructions

AI-generated explanations can still contain errors. Image quality, ambiguous layouts, and extraction mistakes can affect results. Laboratory findings also require appropriate clinical context.

**Medify is not a substitute for a qualified healthcare professional.**

## Deployment

### Frontend

[Vercel — Medify Frontend](https://medical-report-ai-frontend.vercel.app)

### Backend

[Render — Medify API](https://medical-report-ai-a6s6.onrender.com)

The frontend communicates with the deployed FastAPI backend for report analysis.

## Development Workflow

Typical workflow:

```text
Upload report
      ↓
Frontend
      ↓
FastAPI
      ↓
Gemini extraction
      ↓
Image verification
      ↓
Gemini interpretation
      ↓
Structured JSON response
      ↓
Results dashboard
```

## Project Links

- [Live Website](https://medical-report-ai-frontend.vercel.app)
- [GitHub Repository](https://github.com/student-g25/medical-report-ai)
- [Backend API](https://medical-report-ai-a6s6.onrender.com)

## License

This project is currently provided for educational and development purposes.
