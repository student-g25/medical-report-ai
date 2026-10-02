from google import genai
from PIL import Image

print("Starting image analysis...")

try:
    # Create Gemini client
    client = genai.Client()

    # Open our image
    image = Image.open("images/blood test.png")

    print("Image loaded successfully.")
    print("Sending image to Gemini...")

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=[
            image,
            "Describe what you can see in this image in simple language."
        ]
    )

    print("\nSUCCESS!")
    print("\nGemini's response:")
    print(response.text)

except Exception as e:
    print("\nERROR:")
    print(type(e).__name__)
    print(str(e))