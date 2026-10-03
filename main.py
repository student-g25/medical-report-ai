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

from fastapi.responses import StreamingResponse

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
        "https://medical-report-ai-frontend.vercel.app"
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
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
# Streaming progress endpoint
# =========================================================

import json

from fastapi.responses import StreamingResponse
from starlette.concurrency import run_in_threadpool


@app.post("/analyze-report")
async def analyze_report(
    file: UploadFile = File(...)
):

    allowed_types = {
        "image/jpeg",
        "image/png",
        "image/webp"
    }

    async def analysis_stream():

        # =====================================================
        # 1. VALIDATE FILE
        # =====================================================

        if file.content_type not in allowed_types:
            yield json.dumps({
                "type": "error",
                "message": (
                    "Unsupported file type. "
                    "Please upload a JPG, PNG, or WEBP image."
                )
            }) + "\n"
            return

        # =====================================================
        # 2. READ UPLOADED FILE
        # =====================================================

        try:
            image_data = await file.read()

        except Exception as error:

            yield json.dumps({
                "type": "error",
                "message": (
                    "Could not read uploaded file: "
                    f"{str(error)}"
                )
            }) + "\n"
            return

        # =====================================================
        # 3. EMPTY FILE CHECK
        # =====================================================

        if len(image_data) == 0:

            yield json.dumps({
                "type": "error",
                "message": "The uploaded file is empty."
            }) + "\n"
            return

        # =====================================================
        # 4. IMAGE SIZE CHECK
        # =====================================================

        max_size = 10 * 1024 * 1024

        if len(image_data) > max_size:

            yield json.dumps({
                "type": "error",
                "message": "Image is too large. Maximum size is 10 MB."
            }) + "\n"
            return

        # =====================================================
        # PIPELINE START
        # =====================================================

        yield json.dumps({
            "type": "stage",
            "stage": "extract",
            "status": "active",
            "message": "Reading your medical report..."
        }) + "\n"

        # Give the browser a moment to render the active state
        # before starting the actual backend operation.
        import asyncio
        await asyncio.sleep(0.05)

        # =====================================================
        # 5. PASS 1 — RAW EXTRACTION
        # =====================================================

        try:

            extracted_report = await run_in_threadpool(
                extract_report,
                image_data=image_data,
                mime_type=file.content_type
            )

        except Exception as error:

            yield json.dumps({
                "type": "error",
                "stage": "extract",
                "message": (
                    "Medical report extraction failed: "
                    f"{str(error)}"
                )
            }) + "\n"
            return

        # Extraction finished
        yield json.dumps({
            "type": "stage",
            "stage": "extract",
            "status": "complete",
            "message": "Report data extracted successfully."
        }) + "\n"

        await asyncio.sleep(0.05)

        # =====================================================
        # 6. PASS 2 — IMAGE / REPORT VERIFICATION
        # =====================================================

        yield json.dumps({
            "type": "stage",
            "stage": "understand",
            "status": "active",
            "message": "Understanding the report..."
        }) + "\n"

        await asyncio.sleep(0.05)

        try:

            verified_report = await run_in_threadpool(
                verify_report,
                image_data=image_data,
                mime_type=file.content_type,
                extracted_report=extracted_report
            )

        except Exception as error:

            yield json.dumps({
                "type": "error",
                "stage": "understand",
                "message": (
                    "Medical report verification failed: "
                    f"{str(error)}"
                )
            }) + "\n"
            return

        yield json.dumps({
            "type": "stage",
            "stage": "understand",
            "status": "complete",
            "message": "Report information verified."
        }) + "\n"

        await asyncio.sleep(0.05)

        # =====================================================
        # 7. PASS 3 — INTERPRETATION
        # =====================================================

        yield json.dumps({
            "type": "stage",
            "stage": "analyze",
            "status": "active",
            "message": "Analyzing the report..."
        }) + "\n"

        await asyncio.sleep(0.05)

        try:

            interpretation = await run_in_threadpool(
                interpret_report,
                verified_report=verified_report,
                patient_info=extracted_report.patient_info
            )

        except Exception as error:

            yield json.dumps({
                "type": "error",
                "stage": "analyze",
                "message": (
                    "Medical report interpretation failed: "
                    f"{str(error)}"
                )
            }) + "\n"
            return

        yield json.dumps({
            "type": "stage",
            "stage": "analyze",
            "status": "complete",
            "message": "Analysis completed."
        }) + "\n"

        await asyncio.sleep(0.05)

        # =====================================================
        # 8. PREPARING RESULTS
        # =====================================================

        yield json.dumps({
            "type": "stage",
            "stage": "prepare",
            "status": "active",
            "message": "Preparing your results..."
        }) + "\n"

        await asyncio.sleep(0.05)

        # =====================================================
        # 9. BUILD FINAL RESPONSE
        # =====================================================

        result = {
            "filename": file.filename,

            "patient_info": (
                extracted_report
                .patient_info
                .model_dump()
            ),

            "extraction": (
                extracted_report
                .model_dump()
            ),

            "verification": (
                verified_report
                .model_dump()
            ),

            "interpretation": (
                interpretation
                .model_dump()
            )
        }

        yield json.dumps({
            "type": "stage",
            "stage": "prepare",
            "status": "complete",
            "message": "Results are ready."
        }) + "\n"

        # =====================================================
        # 10. FINAL RESULT
        # =====================================================

        yield json.dumps({
            "type": "complete",
            "data": result
        }) + "\n"

    return StreamingResponse(
        analysis_stream(),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )