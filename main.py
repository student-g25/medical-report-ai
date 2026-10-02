# =========================================================
# MAIN.PY
# Medical Report Demystifier API
# =========================================================

import os
from pathlib import Path

from dotenv import load_dotenv

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException
)

from fastapi.middleware.cors import CORSMiddleware


# =========================================================
# LOAD .ENV FROM PROJECT ROOT
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

ENV_FILE = BASE_DIR / ".env"

load_dotenv(
    dotenv_path=ENV_FILE,
    override=True
)


# =========================================================
# CHECK GEMINI API KEY
# =========================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:

    raise RuntimeError(
        f"GEMINI_API_KEY was not found in: {ENV_FILE}"
    )


# =========================================================
# IMPORT AI PIPELINE
# =========================================================

from medical_ai import (
    extract_report,
    verify_report,
    interpret_report
)


# =========================================================
# CREATE FASTAPI APPLICATION
# =========================================================

app = FastAPI(
    title="Medical Report Demystifier API",

    description=(
        "AI-powered multimodal medical report "
        "extraction, verification and explanation system."
    ),

    version="0.5.0"
)


# =========================================================
# CORS
# =========================================================
#
# Allows the teammate's frontend running on another
# local port to communicate with this FastAPI backend.
#
# This is suitable for LOCAL DEVELOPMENT.
# We will restrict the allowed origin when deploying.
# =========================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "*"
    ],

    allow_credentials=False,

    allow_methods=[
        "*"
    ],

    allow_headers=[
        "*"
    ]
)


# =========================================================
# ROOT ENDPOINT
# =========================================================

@app.get("/")
def root():

    return {
        "message": "Medical Report Demystifier API is running",
        "status": "ok"
    }


# =========================================================
# HEALTH CHECK
# =========================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "gemini_configured": True
    }


# =========================================================
# ANALYZE MEDICAL REPORT
# =========================================================

@app.post("/analyze-report")
async def analyze_report(
    file: UploadFile = File(...)
):

    # =====================================================
    # 1. VALIDATE FILE TYPE
    # =====================================================

    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp"
    }

    if file.content_type not in allowed_types:

        raise HTTPException(
            status_code=400,

            detail=(
                "Unsupported file type. "
                "Please upload a JPG, PNG, or WEBP image."
            )
        )


    # =====================================================
    # 2. READ UPLOADED FILE
    # =====================================================

    try:

        image_data = await file.read()

    except Exception as error:

        raise HTTPException(
            status_code=400,

            detail=(
                "Could not read uploaded file: "
                f"{str(error)}"
            )
        )


    # =====================================================
    # 3. CHECK EMPTY FILE
    # =====================================================

    if len(image_data) == 0:

        raise HTTPException(
            status_code=400,

            detail="The uploaded file is empty."
        )


    # =====================================================
    # 4. CHECK IMAGE SIZE
    # =====================================================

    max_size = 10 * 1024 * 1024  # 10 MB

    if len(image_data) > max_size:

        raise HTTPException(
            status_code=413,

            detail=(
                "Image is too large. "
                "Maximum allowed size is 10 MB."
            )
        )


    # =====================================================
    # 5. PASS 1 — RAW EXTRACTION
    # =====================================================

    try:

        extracted_report = extract_report(
            image_data=image_data,
            mime_type=file.content_type
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,

            detail=(
                "Medical report extraction failed: "
                f"{str(error)}"
            )
        )


    # =====================================================
    # 6. PASS 2 — IMAGE VERIFICATION
    # =====================================================

    try:

        verified_report = verify_report(
            image_data=image_data,
            mime_type=file.content_type,
            extracted_report=extracted_report
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,

            detail=(
                "Medical report verification failed: "
                f"{str(error)}"
            )
        )


    # =====================================================
    # 7. PASS 3 — INTERPRETATION
    # =====================================================

    try:

        interpretation = interpret_report(
            verified_report=verified_report,

            patient_info=(
                extracted_report.patient_info
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=500,

            detail=(
                "Medical report interpretation failed: "
                f"{str(error)}"
            )
        )


    # =====================================================
    # 8. FINAL JSON RESPONSE
    # =====================================================

    return {

        # -------------------------------------------------
        # Uploaded file
        # -------------------------------------------------

        "filename": file.filename,


        # -------------------------------------------------
        # Patient information
        # Extracted directly from the report
        # -------------------------------------------------

        "patient_info":
            extracted_report
            .patient_info
            .model_dump(),


        # -------------------------------------------------
        # PASS 1
        # Raw extraction
        # -------------------------------------------------

        "extraction":
            extracted_report
            .model_dump(),


        # -------------------------------------------------
        # PASS 2
        # Verification
        # -------------------------------------------------

        "verification":
            verified_report
            .model_dump(),


        # -------------------------------------------------
        # PASS 3
        # Interpretation
        # -------------------------------------------------

        "interpretation":
            interpretation
            .model_dump()

    }