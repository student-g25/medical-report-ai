# =========================================================
# MEDICAL_AI.PY
# Medical Report Demystifier - AI Pipeline
# =========================================================

import os
import json

from dotenv import load_dotenv

from google import genai
from google.genai import types

from pydantic import BaseModel
from typing import List


# =========================================================
# LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()


# =========================================================
# GEMINI API KEY
# =========================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY was not found in the .env file."
    )


# =========================================================
# GEMINI CLIENT
# =========================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# =========================================================
# PASS 1 — PATIENT INFORMATION
# =========================================================

class PatientInfo(BaseModel):

    age: str

    sex: str


# =========================================================
# PASS 1 — EXTRACTED TEST
# =========================================================

class ExtractedTest(BaseModel):

    name: str

    value: str

    unit: str

    reference_range: str

    visual_text: str

    confidence: str


# =========================================================
# PASS 1 — COMPLETE EXTRACTION
# =========================================================

class ExtractedReport(BaseModel):

    report_type: str

    patient_info: PatientInfo

    tests: List[ExtractedTest]

    visible_notes: List[str]

    extraction_warnings: List[str]


# =========================================================
# PASS 2 — VERIFIED TEST
# =========================================================

class VerifiedTest(BaseModel):

    name: str

    # Original extraction

    original_value: str

    original_unit: str

    original_reference_range: str

    # Verified against original image

    verified_value: str

    verified_unit: str

    verified_reference_range: str

    # Verification state

    verified: bool

    confidence: str

    correction_needed: str

    # Safety gate

    usable_for_interpretation: bool


# =========================================================
# PASS 2 — VERIFIED REPORT
# =========================================================

class VerifiedReport(BaseModel):

    report_type: str

    tests: List[VerifiedTest]

    verification_warnings: List[str]


# =========================================================
# PASS 3 — TEST EXPLANATION
# =========================================================

class TestExplanation(BaseModel):

    name: str

    reported_value: str

    reported_unit: str

    reference_range: str

    status: str

    simple_explanation: str


# =========================================================
# PASS 3 — FRONTEND SECTION
# =========================================================

class InterpretationSection(BaseModel):

    title: str

    icon: str

    tests: List[TestExplanation]


# =========================================================
# PASS 3 — INTERPRETATION REPORT
# =========================================================

class InterpretationReport(BaseModel):

    summary: str

    # Individual explanations
    tests: List[TestExplanation]

    # NEW:
    # Dynamically grouped information for frontend
    sections: List[InterpretationSection]

    important_points: List[str]

    doctor_discussion_questions: List[str]

    limitations: List[str]


# =========================================================
# PASS 1
# RAW DOCUMENT EXTRACTION
# =========================================================

def extract_report(
    image_data: bytes,
    mime_type: str
):

    extraction_prompt = """
You are a medical document data extraction system.

Your ONLY job is to accurately read information that is
VISIBLY PRESENT in the uploaded medical report.

This is a DOCUMENT EXTRACTION task.

It is NOT a medical interpretation task.


=========================================================
DO NOT
=========================================================

DO NOT:

- diagnose anything
- interpret medical conditions
- suggest diseases
- suggest causes
- recommend treatment
- recommend medication
- calculate medical values
- convert units
- invent missing information
- infer information that is not visible


=========================================================
PATIENT INFORMATION
=========================================================

Look for patient demographic information explicitly shown
on the report.

Extract:

- age
- sex/gender

IMPORTANT:

AGE:

If an explicit age is visible, copy it.

If age is not visible or cannot be reliably read:

age = "unknown"

NEVER calculate or guess the age.


SEX/GENDER:

If sex/gender is explicitly visible, copy it.

If sex/gender is not visible or cannot be reliably read:

sex = "unknown"

NEVER infer sex/gender from:

- the patient's name
- appearance
- pronouns
- other indirect information


=========================================================
LABORATORY TESTS
=========================================================

For every laboratory test:

1. Copy the test name exactly as visible.

2. Copy the reported value exactly as visible.

3. Copy the unit exactly as visible.

4. Copy the reference range exactly as visible.

5. Keep the value, unit and reference range associated
   with the SAME test row.

6. Never borrow information from another row.

7. Never invent a value.

8. Never invent a unit.

9. Never invent a reference range.

10. Never calculate anything.

11. Never convert units.

If something cannot be read confidently:

write:

"unclear"


=========================================================
VISUAL TEXT
=========================================================

For every test, provide visual_text containing the
important text visibly associated with that test row.

This helps the later verification stage compare the
extraction against the original image.


=========================================================
CONFIDENCE
=========================================================

Use:

"high"

when the information is clearly readable.

"medium"

when the information is mostly readable but there is
some uncertainty.

"low"

when the information is difficult to read or associate
with the correct row.


=========================================================
VISIBLE NOTES
=========================================================

Extract clearly visible notes, comments or observations
from the document.

Do not interpret them.


=========================================================
EXTRACTION WARNINGS
=========================================================

Record problems such as:

- unclear text
- overlapping rows
- unclear reference range
- unclear unit
- poor image quality
- ambiguous row alignment


=========================================================
IMPORTANT
=========================================================

Return ONLY information that is supported by the uploaded
image.

Do not provide medical advice.

Do not interpret the results.
"""

    response = client.models.generate_content(

        model="gemini-3.5-flash-lite",

        contents=[
            extraction_prompt,

            types.Part.from_bytes(
                data=image_data,
                mime_type=mime_type
            )
        ],

        config=types.GenerateContentConfig(

            response_mime_type="application/json",

            response_schema=ExtractedReport,

            temperature=0
        )
    )

    return response.parsed


# =========================================================
# PASS 2
# IMAGE-BASED VERIFICATION
# =========================================================

def verify_report(
    image_data: bytes,
    mime_type: str,
    extracted_report: ExtractedReport
):

    extracted_json = extracted_report.model_dump_json(
        indent=2
    )

    verification_prompt = f"""
You are a medical-document extraction verification system.

Your ONLY task is to verify candidate extraction data
against the ORIGINAL uploaded medical report image.

This is NOT a medical interpretation task.


=========================================================
CANDIDATE EXTRACTION
=========================================================

{extracted_json}


=========================================================
VERIFICATION RULE
=========================================================

Look directly at the ORIGINAL IMAGE.

For EVERY laboratory test:

1. Find the corresponding test row.

2. Verify the test name.

3. Verify the reported value.

4. Verify the unit.

5. Verify the reference range.

6. Confirm that the value, unit and reference range
   belong to the SAME test row.

7. Never borrow information from another row.

8. Never guess missing information.


=========================================================
ORIGINAL DATA
=========================================================

Copy the Pass 1 extraction into:

original_value

original_unit

original_reference_range


=========================================================
VERIFIED DATA
=========================================================

Provide the information actually supported by the
original image:

verified_value

verified_unit

verified_reference_range

If something cannot be reliably determined:

write:

"unclear"

NEVER GUESS.


=========================================================
VERIFICATION STATE
=========================================================

Set:

verified = true

ONLY when the important information can be reliably
associated with the correct test row.

Otherwise:

verified = false


=========================================================
CONFIDENCE
=========================================================

Use:

"high"

Clearly readable and correctly associated.

"medium"

Mostly readable but there is some uncertainty.

"low"

Difficult to read or associate confidently.


=========================================================
CORRECTION NEEDED
=========================================================

If the original extraction is correct:

correction_needed = "none"

If something was wrong, briefly describe the correction.

Examples:

"Corrected unit."

"Corrected reference range."

"Reference range and unit alignment correction."

"Unable to verify unit."


=========================================================
INTERPRETATION SAFETY GATE
=========================================================

Set:

usable_for_interpretation = true

ONLY when ALL of these are true:

- verified is true
- value is reliably readable
- unit is reliably readable
- relevant reference range is reliably readable
- value and reference range belong to the same test

Otherwise:

usable_for_interpretation = false


=========================================================
IMPORTANT
=========================================================

This stage verifies WHAT THE DOCUMENT SAYS.

It does NOT determine what the result means medically.

Do NOT diagnose.

Do NOT recommend treatment.

Do NOT provide medical advice.
"""

    response = client.models.generate_content(

        model="gemini-3.5-flash-lite",

        contents=[
            verification_prompt,

            types.Part.from_bytes(
                data=image_data,
                mime_type=mime_type
            )
        ],

        config=types.GenerateContentConfig(

            response_mime_type="application/json",

            response_schema=VerifiedReport,

            temperature=0
        )
    )

    return response.parsed


# =========================================================
# PASS 3
# INTERPRET VERIFIED RESULTS
# =========================================================

def interpret_report(
    verified_report: VerifiedReport,
    patient_info: PatientInfo
):

    # =====================================================
    # SAFETY GATE
    # =====================================================

    usable_tests = []

    for test in verified_report.tests:

        if (
            test.verified is True
            and test.usable_for_interpretation is True
        ):

            usable_tests.append(test)


    # =====================================================
    # IF NOTHING PASSED VERIFICATION
    # =====================================================

    if not usable_tests:

        return InterpretationReport(

            summary=(
                "No laboratory results passed the "
                "verification checks required for "
                "automatic explanation."
            ),

            tests=[],

            sections=[],

            important_points=[
                (
                    "Some report information could not "
                    "be reliably verified from the image."
                )
            ],

            doctor_discussion_questions=[
                (
                    "Could the original report be reviewed "
                    "manually with a qualified healthcare "
                    "professional?"
                )
            ],

            limitations=[
                (
                    "Unverified laboratory values were "
                    "excluded from automatic interpretation."
                ),

                (
                    "This system provides educational "
                    "information and does not provide "
                    "a medical diagnosis."
                )
            ]
        )


    # =====================================================
    # PREPARE VERIFIED DATA
    # =====================================================

    verified_tests = []

    for test in usable_tests:

        verified_tests.append({

            "name": test.name,

            "value": test.verified_value,

            "unit": test.verified_unit,

            "reference_range":
                test.verified_reference_range
        })


    # =====================================================
    # PATIENT CONTEXT
    # =====================================================

    user_context = {

        "age": patient_info.age,

        "sex": patient_info.sex
    }


    # =====================================================
    # JSON FOR GEMINI
    # =====================================================

    verified_json = json.dumps(
        verified_tests,
        indent=2,
        ensure_ascii=False
    )

    context_json = json.dumps(
        user_context,
        indent=2,
        ensure_ascii=False
    )


    # =====================================================
    # INTERPRETATION PROMPT
    # =====================================================

    interpretation_prompt = f"""
You are a medical-report explanation assistant.

Your job is to explain VERIFIED laboratory results in
simple, understandable language.

The report has already passed a separate document
verification step.


=========================================================
PATIENT INFORMATION
=========================================================

{context_json}

Use the available age and sex information only when it
is relevant to explaining the report.

If the information is "unknown", do not guess it.


=========================================================
VERIFIED LABORATORY RESULTS
=========================================================

{verified_json}


=========================================================
STRICT RULES
=========================================================

1. NEVER change a reported value.

2. NEVER change a reported unit.

3. NEVER change a reference range.

4. Use the reference range supplied by the report.

5. Do not invent a reference range.

6. Do not invent missing information.

7. Do not diagnose diseases.

8. Do not claim that one laboratory result proves a disease.

9. Do not recommend medication.

10. Do not tell the user to start or stop medication.

11. Do not provide treatment instructions.

12. Explain medical terminology in simple language.

13. Keep explanations understandable for a general user.

14. Clearly distinguish the report's findings from
    questions that should be discussed with a doctor.

15. Do not speculate about the user's medical history.

16. Do not unnecessarily frighten the user.

17. Do not make conclusions about the user's overall
    health from a single laboratory result.

18. This is educational information, NOT a diagnosis.


=========================================================
STATUS
=========================================================

For each test:

If the value is within the supplied reference range:

status = "within stated reference range"

If it is below the supplied reference range:

status = "below stated reference range"

If it is above the supplied reference range:

status = "above stated reference range"

If the status cannot be determined reliably:

status = "cannot be determined"

Do not create your own reference ranges.


=========================================================
EXPLANATION
=========================================================

For EVERY verified test, provide a concise,
plain-language explanation.

The explanation should tell the user:

1. What the metric generally measures.

2. What its result/status means relative to the
   reference range supplied by THIS report.

Keep this educational.

Do not turn the explanation into a diagnosis.

Example style:

"Hemoglobin helps carry oxygen around the body."

"Platelets are blood components that help with clotting."

"TSH is a hormone used to help assess thyroid function."

Do NOT copy these examples unless the uploaded report
actually contains those metrics.


=========================================================
DYNAMIC REPORT SECTIONS
=========================================================

The frontend will display the results in visually
separated sections.

Create logical sections based ONLY on the verified tests
actually present in this report.

Examples of possible section types include:

- Blood & Blood Cells
- White Blood Cell Distribution
- Thyroid Function
- Liver Function
- Kidney Function
- Lipid Profile
- Glucose & Diabetes Markers
- Electrolytes
- Urinalysis
- Vitamins & Minerals
- Hormones
- Cardiac Markers
- Other Laboratory Results

IMPORTANT:

These are ONLY examples.

Do NOT create a section unless the verified tests
actually support it.

If the report contains unfamiliar or mixed laboratory
tests, create a neutral section such as:

"Laboratory Results"

or another accurate title based on the actual tests.

DO NOT invent tests.

DO NOT move a test into an unrelated category.

Every verified test MUST appear in exactly ONE section.


=========================================================
SECTION ICON
=========================================================

For each section provide a short icon identifier.

Use identifiers such as:

"blood"
"immune"
"thyroid"
"liver"
"kidney"
"lipids"
"glucose"
"electrolytes"
"vitamins"
"hormones"
"heart"
"urine"
"general"

The icon identifier is ONLY for frontend presentation.

Do not use an icon identifier as medical evidence.


=========================================================
SECTION CONTENT
=========================================================

Each section must contain:

- title
- icon
- tests

The tests must contain the complete TestExplanation
information.

Do not duplicate or omit verified tests.


=========================================================
OVERALL SUMMARY
=========================================================

Provide a short, neutral summary of the verified results.

Do not claim that the summary represents a diagnosis.


=========================================================
IMPORTANT POINTS
=========================================================

List the findings that may be useful for the user to
understand or discuss with a healthcare professional.

Only mention findings supported by the verified data.


=========================================================
DOCTOR DISCUSSION QUESTIONS
=========================================================

Provide useful questions the user can discuss with their
doctor.

Do not provide treatment instructions.


=========================================================
LIMITATIONS
=========================================================

Mention relevant limitations such as:

- laboratory results need clinical context
- reference ranges can vary between laboratories
- image-based extraction can contain errors
- this system is not a substitute for a healthcare
  professional


=========================================================
FINAL SAFETY REQUIREMENT
=========================================================

Only use the verified laboratory results supplied above.

Do not introduce medical values that are not present.

Do not introduce diagnoses.

Do not invent patient information.

Do not invent laboratory tests.

Do not invent reference ranges.
"""


    # =====================================================
    # GEMINI INTERPRETATION
    # =====================================================

    response = client.models.generate_content(

        model="gemini-3.5-flash-lite",

        contents=interpretation_prompt,

        config=types.GenerateContentConfig(

            response_mime_type="application/json",

            response_schema=InterpretationReport,

            temperature=0.1
        )
    )

    return response.parsed