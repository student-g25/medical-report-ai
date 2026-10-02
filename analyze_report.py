from google import genai
from google.genai import types
from pydantic import BaseModel
from typing import List


# -----------------------------
# 1. Define our output structure
# -----------------------------

class TestResult(BaseModel):
    name: str
    value: str
    unit: str
    reference_range: str
    status: str
    simple_explanation: str


class MedicalReport(BaseModel):
    report_type: str
    tests: List[TestResult]
    important_observations: List[str]
    doctor_discussion_questions: List[str]
    limitations: List[str]


# -----------------------------
# 2. Create Gemini client
# -----------------------------

client = genai.Client()


# -----------------------------
# 3. Load image
# -----------------------------

image = open("images/blood test.png", "rb")


# -----------------------------
# 4. Instructions
# -----------------------------

prompt = """
Analyze this medical report image for educational explanation.

Important rules:

- Extract only information that is actually visible in the image.
- Do not invent missing values.
- Do not invent units.
- Do not invent reference ranges.
- If a value, unit, or reference range cannot be read reliably, write "unclear".
- Use the reference range printed on the report when available.
- Do not use a generic reference range from your own knowledge when the report provides none.
- Do not diagnose the patient.
- Do not claim that an abnormal result proves a disease.
- Explain medical terminology in simple language.
- Mention uncertainty when the image is unclear.
- Include questions that the patient could discuss with a qualified doctor.
"""


# -----------------------------
# 5. Ask Gemini
# -----------------------------

response = client.models.generate_content(
    model="gemini-3.5-flash-lite",

    contents=[
        prompt,
        types.Part.from_bytes(
            data=image.read(),
            mime_type="image/png"
        )
    ],

    config=types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=MedicalReport,
        temperature=0.1
    )
)


# -----------------------------
# 6. Read structured response
# -----------------------------

print("\n========== MEDICAL REPORT ==========\n")

print(response.text)

print("\n========== PARSED DATA ==========\n")

report = response.parsed

print(report)