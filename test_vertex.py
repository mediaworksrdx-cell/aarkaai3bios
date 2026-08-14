import config
from modules.external_agents import stream_gemini_response

print("Testing Vertex AI stream_gemini_response...")
for chunk in stream_gemini_response("Hello, respond in 5 words"):
    print(chunk, end="", flush=True)
print("\n--- TEST COMPLETED ---")
