import os
from google import genai
from dotenv import load_dotenv


if __name__ == '__main__':
    load_dotenv()

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    print("🔍 Checking available models for your key...")
    try:
        # List all models
        for m in client.models.list():
            if "generateContent" in m.supported_actions:
                print(f"✅ Available: {m.name}")
    except Exception as e:
        print(f"❌ Error: {e}")