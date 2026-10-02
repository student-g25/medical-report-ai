from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List
from pathlib import Path
import json


# =========================================================
# 1. OUTPUT STRUCTURES
# =========================================================

class TestExplanation(BaseModel):
    name: str
    reported_value: str
    reported_unit: str
    reference_range: str

    status: str
    simple_explanation: str


class InterpretationReport(BaseModel):
    summary: str
    tests: List[TestExplanation]
    important_points: List[str]
    doctor_discussion_questions: List[str]
    limitations: List[str]


# =========================================================
# 2. PROJECT PATHS
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "verified_report.json"
USER_CONTEXT_FILE = BASE_DIR / "user_context.json"


# =========================================================
# 3. CHECK REQUIRED FILES
# =========================================================

if not INPUT_FILE.exists():
    print("ERROR: verified_report.json was not found.")
    print("Run extract_report.py first.")
    raise SystemExit(1)


if not USER_CONTEXT_FILE.exists():
    print("ERROR: user_context.json was not found.")
    raise SystemExit(1)


# =========================================================
# 4. LOAD VERIFIED REPORT
# =========================================================

with open(INPUT_FILE, "r", encoding="utf-8") as file:
    verified_report = json.load(file)


# =========================================================
# 5. LOAD USER CONTEXT
# =========================================================

with open(USER_CONTEXT_FILE, "r", encoding="utf-8") as file:
    user_context = json.load(file)


# =========================================================
# 6. KEEP ONLY VERIFIED + USABLE RESULTS
# =========================================================

usable_tests = []

for test in verified_report.get("tests", []):

    if (
        test.get("verified") is True
        and test.get("usable_for_interpretation") is True
    ):
        usable_tests.append(test)


# =========================================================
# 7. STOP IF NOTHING IS SAFE TO INTERPRET
# =========================================================

if not usable_tests:

    print()
    print("=" * 60)
    print("NO RELIABLY INTERPRETABLE RESULTS")
    print("=" * 60)
    print()

    print(
        "The report did not contain enough verified information "
        "for automatic explanation."
    )

    print()

    print(
        "The original report should be reviewed by a qualified "
        "healthcare professional."
    )

    raise SystemExit(0)


# =========================================================
# 8. CREATE GEMINI CLIENT
# =========================================================

client = genai.Client()


# =========================================================
# 9. PREPARE VERIFIED DATA
# =========================================================

verified_data_for_ai = {
    "report_type": verified_report.get(
        "report_type",
        "unclear"
    ),
    "tests": usable_tests
}


context_for_ai = {
    "age": user_context.get(
        "age",
        "unknown"
    ),
    "sex": user_context.get(
        "sex",
        "unknown"
    )
}


verified_json = json.dumps(
    verified_data_for_ai,
    indent=4,
    ensure_ascii=False
)


context_json = json.dumps(
    context_for_ai,
    indent=4,
    ensure_ascii=False
)


# =========================================================
# 10. INTERPRETATION PROMPT
# =========================================================

prompt = f"""
You are a medical-report explanation assistant.

Your task is to explain VERIFIED laboratory information
in simple, age-appropriate, patient-friendly language.

The laboratory information below has already passed a
separate document verification step.

=========================================================
USER CONTEXT
=========================================================

{context_json}

Use the user context ONLY to make the explanation
appropriate for the user's age and context.

The user context must NOT be used to change, replace,
invent, or reinterpret the laboratory values.

=========================================================
VERIFIED REPORT DATA
=========================================================

{verified_json}


=========================================================
IMPORTANT RULES
=========================================================

1. NEVER change a reported value.

2. NEVER change a reported unit.

3. NEVER change a reference range.

4. NEVER invent missing information.

5. Use the reference range supplied in the verified report.

6. Do not substitute a generic reference range when the
   report's reference range is available.

7. If a reference range is unclear, say so.

8. Do not diagnose a disease.

9. Do not claim that an abnormal laboratory result proves
   a particular disease.

10. Do not recommend medication or treatment.

11. Do not tell the user to start or stop medication.

12. Explain medical terminology in simple language.

13. Keep the explanation appropriate for the user's age.

14. Avoid unnecessarily frightening language.

15. Clearly distinguish between:
    - what the report actually shows
    - what may need discussion with a healthcare professional

16. Do not speculate about the user's personal medical history.

17. If a result is outside the reference range printed on
    the report, describe it as:

    "above the stated reference range"

    or

    "below the stated reference range"

18. If a result is inside the reference range printed on
    the report, describe it as:

    "within the stated reference range"

19. Do not convert units.

20. Do not perform unnecessary calculations.

21. If there is insufficient information to determine the
    status, use:

    "unclear"

22. Do not use the user's age to invent a new reference
    range.

23. The verified report remains the source of truth for
    the extracted values.

24. This is educational information and is NOT a diagnosis.

25. If an important result appears concerning or unclear,
    explain that the user should discuss it with a qualified
    healthcare professional rather than giving a diagnosis.


=========================================================
OUTPUT REQUIREMENTS
=========================================================

For every verified and usable test:

- Keep the original test name.
- Keep the original reported value.
- Keep the original unit.
- Keep the original reference range.
- Give a status.
- Give a simple explanation.

Also provide:

- A short overall summary.
- Important points worth discussing with a doctor.
- Questions the user could ask a doctor.
- Limitations and uncertainties.

Do not include tests that were rejected by the verification
or safety gate.

Remain educational, cautious, and age-appropriate.
"""


# =========================================================
# 11. ASK GEMINI FOR STRUCTURED EXPLANATION
# =========================================================

response = client.models.generate_content(
    model="gemini-3.5-flash-lite",

    contents=prompt,

    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=InterpretationReport,
        temperature=0.1
    )
)


# =========================================================
# 12. GET STRUCTURED RESULT
# =========================================================

interpretation = response.parsed


# =========================================================
# 13. DISPLAY SUMMARY
# =========================================================

print()
print("=" * 60)
print("MEDICAL REPORT EXPLANATION")
print("=" * 60)
print()

print("SUMMARY")
print()
print(interpretation.summary)


# =========================================================
# 14. DISPLAY TEST RESULTS
# =========================================================

print()
print("=" * 60)
print("TEST RESULTS")
print("=" * 60)
print()


for test in interpretation.tests:

    print(f"Test: {test.name}")
    print(f"Reported value: {test.reported_value}")
    print(f"Unit: {test.reported_unit}")
    print(f"Reference range: {test.reference_range}")
    print(f"Status: {test.status}")
    print(f"Explanation: {test.simple_explanation}")

    print("-" * 60)


# =========================================================
# 15. IMPORTANT POINTS
# =========================================================

print()
print("=" * 60)
print("IMPORTANT POINTS")
print("=" * 60)
print()

for point in interpretation.important_points:
    print(f"- {point}")


# =========================================================
# 16. QUESTIONS FOR A DOCTOR
# =========================================================

print()
print("=" * 60)
print("QUESTIONS TO DISCUSS WITH A DOCTOR")
print("=" * 60)
print()

for question in interpretation.doctor_discussion_questions:
    print(f"- {question}")


# =========================================================
# 17. LIMITATIONS
# =========================================================

print()
print("=" * 60)
print("LIMITATIONS")
print("=" * 60)
print()

for limitation in interpretation.limitations:
    print(f"- {limitation}")


# =========================================================
# 18. FINAL DISCLAIMER
# =========================================================

print()
print("=" * 60)
print("EDUCATIONAL INFORMATION — NOT A DIAGNOSIS")
print("=" * 60)
print()