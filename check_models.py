from google import genai
import config

try:
    client = genai.Client(
        vertexai=True,
        api_key=config.GEMINI_API_KEY,
    )
    print("Listing models with vertexai=True:")
    for m in client.models.list():
        print(" -", m.name)
except Exception as e:
    print("Error listing with vertexai=True:", e)

try:
    client_std = genai.Client(
        api_key=config.GEMINI_API_KEY,
    )
    print("\nListing models standard:")
    for m in client_std.models.list():
        print(" -", m.name)
except Exception as e:
    print("Error listing standard:", e)
