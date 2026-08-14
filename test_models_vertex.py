import config
from google import genai

client = genai.Client(
    vertexai=True,
    project=config.VERTEX_PROJECT,
    location=config.VERTEX_LOCATION,
)

print("--- AVAILABLE VERTEX AI MODELS ---")
try:
    for m in client.models.list():
        if "gemini" in m.name.lower():
            print(f"Model: {m.name}")
except Exception as e:
    print(f"Error listing models: {e}")

print("\n--- TESTING SPECIFIC MODELS ---")
test_models = [
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-1.5-flash",
    "gemini-1.5-pro",
    "gemini-3.5-flash",
    "gemini-3.1-flash",
]

for model_name in test_models:
    try:
        res = client.models.generate_content(
            model=model_name,
            contents="Say hi",
        )
        print(f"✅ {model_name}: SUCCESS -> {res.text.strip()}")
    except Exception as err:
        print(f"❌ {model_name}: FAILED -> {err}")
