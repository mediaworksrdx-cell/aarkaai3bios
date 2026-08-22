import sys
sys.path.insert(0, '/home/ubuntu/aarkaai3b')
import pipeline
import logging

logging.basicConfig(level=logging.INFO)

print("Starting direct pipeline query test...")
try:
    response = pipeline.process_query(
        query="Hello? Who are you?",
        user_id="test_user",
        session_id="test_session"
    )
    print("\n--- TEST SUCCESSFUL ---")
    print("Detected Language:", response.detected_language)
    print("Intent:", response.intent)
    print("Processing Time:", response.processing_time)
    print("Sources:", response.sources)
    print("Response:")
    print(response.response)
except Exception as e:
    print("\n--- TEST FAILED ---")
    import traceback
    traceback.print_exc()
