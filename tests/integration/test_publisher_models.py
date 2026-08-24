import config
from google import genai

client = genai.Client(
    vertexai=True,
    project=config.VERTEX_PROJECT,
    location=config.VERTEX_LOCATION,
)

test_models = [
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.1-pro-preview",
    "gemini-3.7-flash",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
]

print("--- TESTING SPECIFIC VERTEX PUBLISHER MODELS ---")
for model_name in test_models:
    try:
        res = client.models.generate_content(
            model=model_name,
            contents="Say hi in 5 words",
        )
        print(f"✅ {model_name}: SUCCESS -> {res.text.strip()}")
    except Exception as err:
        print(f"❌ {model_name}: FAILED -> {err}")
