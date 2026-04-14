import os
import uvicorn
import config

if __name__ == "__main__":
    from main import app
    import threading
    import time
    import requests

    def run_server():
        uvicorn.run(app, host="127.0.0.1", port=5001, log_level="error")

    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(5)  # Wait for boot and model stub loads

    try:
        data = {
            "user_id": "rthshr",
            "session_id": "1",
            "prompt": "What is EBITDA and why is it important"
        }
        print("Sending payload...")
        resp = requests.post("http://127.0.0.1:5001/prompt", json=data)
        print("Status:", resp.status_code)
        print("Text:", resp.text)
    except Exception as e:
        print("Error:", e)
