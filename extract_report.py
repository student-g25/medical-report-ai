from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List
import json


# =========================================================
# 1. DATA STRUCTURES
# =========================================================

class ExtractedTest(BaseModel):
    name: str
    value: str
    unit: str
    reference_range: str
    visual_text: str
    confidence: str


class ExtractedReport(BaseModel):
    report_type: str
    tests: List[ExtractedTest]
    visible_notes: List[str]
    extraction_warnings: List[str]


class VerifiedTest(BaseModel):
    name: str

    # What Pass 1 originally extracted
    original_value: str
    original_unit: str
    original_reference_range: str

    # What Pass 2 determines is actually supported
    # by the original image
    verified_value: str
    verified_unit: str
    verified_reference_range: str

    verified: bool
    confidence: str
    correction_needed: str

    usable_for_interpretation: bool


class VerifiedReport(BaseModel):
    report_type: str
    tests: List[VerifiedTest]
    verification_warnings: List[str]


# =========================================================
# 2. CREATE GEMINI CLIENT
# =========================================================

client = genai.Client()


# =========================================================
# 3. LOAD REPORT IMAGE
# =========================================================

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
IMAGE_PATH = BASE_DIR / "images" / "blood test.png"

with open(IMAGE_PATH, "rb") as image_file:
    image_data = image_file.read()


# =========================================================
# 4. PASS 1 — RAW EXTRACTION
# =========================================================

extraction_prompt = """
You are a medical document data extraction system.

Your ONLY job is to accurately read information that is
VISIBLY PRESENT in the uploaded medical report.

This is a document extraction task, NOT a medical
interpretation task.

DO NOT:

- diagnose anything
- interpret medical conditions
- decide whether a result is dangerous
- suggest diseases
- suggest causes
- recommend treatment
- calculate medical values
- convert units
- invent missing information

For every laboratory test:

1. Copy the test name exactly as visible.
2. Copy the reported value exactly as visible.
3. Copy the unit exactly as visible.
4. Copy the reference range exactly as visible.
5. Keep the value, unit, and reference range associated
   with the SAME test row.
6. Never borrow information from another row.
7. Never invent a value.
8. Never invent a unit.
9. Never invent a reference range.
10. Never calculate or convert anything.

If a value cannot be read confidently:

    value = "unclear"

If a unit cannot be read confidently:

    unit = "unclear"

If a reference range cannot be read confidently:

    reference_range = "unclear"

For visual_text:

Include the visible text from the relevant row that
supports the extracted test name, value, unit, and
reference range.

For confidence:

Use:

"high"
    The row is clearly readable and the fields are
    clearly associated.

"medium"
    The information is readable but there is some
    uncertainty.

"low"
    The row or association between fields is difficult
    to determine.

If the document layout makes it uncertain which
reference range belongs to which test, mark confidence
as "low" and explain the issue in extraction_warnings.

Also extract clearly visible notes or comments from the
report.

Return RAW DOCUMENT DATA ONLY.
"""


extraction_response = client.models.generate_content(
    model="gemini-3.5-flash-lite",

    contents=[
        extraction_prompt,

        types.Part.from_bytes(
            data=image_data,
            mime_type="image/png"
        )
    ],

    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=ExtractedReport,
        temperature=0
    )
)


# Get structured Pass 1 result
extracted_report = extraction_response.parsed


# =========================================================
# 5. PASS 2 — VISUAL VERIFICATION
# =========================================================

verification_prompt = f"""
You are a medical-document extraction verification system.

Your task is ONLY to verify the candidate extraction
against the ORIGINAL uploaded image.

DO NOT interpret medical meaning.

DO NOT diagnose.

DO NOT decide whether a result is normal or abnormal.

DO NOT suggest diseases.

DO NOT suggest causes.

DO NOT recommend treatment.

The candidate extraction from Pass 1 is:

{extracted_report.model_dump_json(indent=2)}


For EVERY test:

1. Look directly at the original image.
2. Find the corresponding test row.
3. Verify the test name.
4. Verify the reported value.
5. Verify the unit.
6. Verify the reference range.
7. Make sure the value, unit, and reference range
   belong to THIS test.
8. Make sure information from a neighboring row has
   not been accidentally assigned to this test.
9. Do not use medical knowledge to fill missing information.
10. If something cannot be confidently verified from
    the image, write "unclear".
11. Never guess.


ORIGINAL FIELDS

Put the information from Pass 1 into:

original_value
original_unit
original_reference_range


VERIFIED FIELDS

After examining the original image, put the information
that is actually supported by the image into:

verified_value
verified_unit
verified_reference_range


IMPORTANT:

If the original extraction was wrong, correct it ONLY
using information that is visibly present in the image.

For example, if Pass 1 incorrectly assigned a reference
range from another row:

original_reference_range:
    the incorrectly extracted range

verified_reference_range:
    the range actually belonging to this row

If the correct information cannot be determined
confidently from the image:

verified_value = "unclear"

or

verified_unit = "unclear"

or

verified_reference_range = "unclear"


VERIFIED FIELD

Set:

verified = true

ONLY when the information can be reliably associated
with the correct row in the image.

Then determine:

usable_for_interpretation = true

ONLY when there is enough reliable information to safely
perform a basic comparison against the report's own
reference range.

For example, if the value or reference range is unclear,
set:

usable_for_interpretation = false

If a unit is essential to understanding the value and
the unit is unclear, set:

usable_for_interpretation = false

Never guess missing information just to make
usable_for_interpretation true.

Set:

verified = false

when:

- the row is unclear
- the value cannot be confirmed
- the unit cannot be confirmed
- the reference range cannot be confirmed
- information appears to have been mixed between rows
- the image quality prevents reliable verification


CONFIDENCE

Use:

"high"
    Clearly visible and correctly associated.

"medium"
    Mostly readable but there is some uncertainty.

"low"
    Difficult to read or associate confidently.


CORRECTION_NEEDED

Use:

"none"

when the original extraction was correct.

Otherwise briefly describe what was corrected.

For example:

"Corrected reference range alignment."

or:

"Corrected unit."

or:

"Unable to verify unit."


SAFETY RULE

If something cannot be confidently determined from
the image, DO NOT GUESS.

Use "unclear".

This is a DOCUMENT VERIFICATION task,
NOT a medical interpretation task.
"""


verification_response = client.models.generate_content(
    model="gemini-3.5-flash-lite",

    contents=[
        verification_prompt,

        types.Part.from_bytes(
            data=image_data,
            mime_type="image/png"
        )
    ],

    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=VerifiedReport,
        temperature=0
    )
)


# Get structured Pass 2 result
verified_report = verification_response.parsed


# =========================================================
# 6. DISPLAY RAW EXTRACTION
# =========================================================

print("\n")
print("=" * 60)
print("RAW EXTRACTION")
print("=" * 60)
print()


for test in extracted_report.tests:

    print(f"Test:       {test.name}")
    print(f"Value:      {test.value}")
    print(f"Unit:       {test.unit}")
    print(f"Reference:  {test.reference_range}")
    print(f"Confidence: {test.confidence}")
    print(f"Visual text: {test.visual_text}")

    print("-" * 60)


# =========================================================
# 7. DISPLAY VERIFIED EXTRACTION
# =========================================================

print("\n")
print("=" * 60)
print("VERIFIED EXTRACTION")
print("=" * 60)
print()


for test in verified_report.tests:

    print(f"Test: {test.name}")

    print()
    print("ORIGINAL EXTRACTION")
    print(f"Value:      {test.original_value}")
    print(f"Unit:       {test.original_unit}")
    print(f"Reference:  {test.original_reference_range}")

    print()
    print("VERIFIED DATA")
    print(f"Value:      {test.verified_value}")
    print(f"Unit:       {test.verified_unit}")
    print(f"Reference:  {test.verified_reference_range}")

    print()
    print(f"Verified:   {test.verified}")
    print(f"Confidence: {test.confidence}")
    print(f"Correction: {test.correction_needed}")
    print(
    f"Usable for interpretation: "
    f"{test.usable_for_interpretation}"
)

    print("-" * 60)


# =========================================================
# 8. DISPLAY VERIFICATION WARNINGS
# =========================================================

print("\n")
print("=" * 60)
print("VERIFICATION WARNINGS")
print("=" * 60)
print()


if verified_report.verification_warnings:

    for warning in verified_report.verification_warnings:
        print(f"- {warning}")

else:

    print("No verification warnings.")


print("\n")
print("=" * 60)
print("EXTRACTION COMPLETE")
print("=" * 60)

# =========================================================
# 9. SAVE VERIFIED DATA
# =========================================================

output_path = BASE_DIR / "verified_report.json"

with open(output_path, "w", encoding="utf-8") as output_file:
    json.dump(
        verified_report.model_dump(),
        output_file,
        indent=4,
        ensure_ascii=False
    )

print()
print(f"Verified report saved to: {output_path}")