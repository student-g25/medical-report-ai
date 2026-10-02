from google import genai

print("Starting Gemini test...")

try:
    client = genai.Client()

    print("Client created successfully.")
    print("Testing Gemini...")

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents="Say hello in one short sentence."
    )

    print("\nSUCCESS!")
    print(response.text)

except Exception as e:
    print("\nERROR:")
    print(type(e).__name__)
    print(str(e))