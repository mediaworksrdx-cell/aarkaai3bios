import json
import time
import requests
import uuid

def stream_turn(base_url, user_id, session_id, query, turn_num):
    print(f"\n--- Turn {turn_num} Query: '{query}' ---")
    payload = {
        "query": query,
        "user_id": user_id,
        "session_id": session_id,
        "stream": True
    }
    
    full_text = ""
    intent = ""
    sources = []
    
    with requests.post(f"{base_url}/prompt/stream", json=payload, stream=True, timeout=120) as resp:
        if resp.status_code != 200:
            print(f"Error: status code {resp.status_code}, text: {resp.text[:200]}")
            return ""
        for line in resp.iter_lines():
            if line:
                line_str = line.decode("utf-8")
                if line_str.startswith("data: "):
                    try:
                        data = json.loads(line_str[6:])
                        msg_type = data.get("type")
                        if msg_type == "metadata":
                            intent = data.get("intent")
                            sources = data.get("sources", [])
                        elif msg_type == "content":
                            tok = data.get("token", "")
                            full_text += tok
                            print(tok, end="", flush=True)
                    except Exception:
                        pass

    print(f"\n[Turn {turn_num} End | Intent: {intent} | Sources: {sources}]")
    # Brief wait to ensure background persistence thread completes DB write
    time.sleep(2.0)
    return full_text

def test_api():
    base_url = "http://localhost:5000"
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"

    print("=" * 60)
    print("TESTING LIVE AARKA SSE STREAM (/prompt/stream)")
    print(f"User ID: {user_id} | Session ID: {session_id}")
    print("=" * 60)

    # 5 conversational turns to build 10 messages of history (5 user + 5 assistant)
    turns = [
        "My secret project code is Project Nebula and target valuation is 50 million dollars.",
        "We are choosing MongoDB with ChromaDB as our database stack.",
        "For event streaming, we decided on Apache Kafka with Apache Flink.",
        "Our cloud infrastructure will be GCP compute instances.",
        "We are using Aarka native neural engine running locally via llama.cpp."
    ]

    for idx, q in enumerate(turns, 1):
        stream_turn(base_url, user_id, session_id, q, idx)

    # Turn 6: The critical follow-up test across the 10 messages of history
    followup_q = "Now tell me, what was the secret project code and target valuation I told you in the very beginning?"
    final_output = stream_turn(base_url, user_id, session_id, followup_q, 6)

    print("\n" + "=" * 60)
    print("FOLLOW-UP RECALL VERIFICATION:")
    print("=" * 60)
    recalled_nebula = "nebula" in final_output.lower()
    recalled_50m = ("50" in final_output.lower() and "million" in final_output.lower()) or "50m" in final_output.lower()

    print(f"Recalled 'Project Nebula': {recalled_nebula}")
    print(f"Recalled '50 million':    {recalled_50m}")

    if recalled_nebula and recalled_50m:
        print("\n>>> SUCCESS: Live Aarka /prompt/stream handled 10-message history & accurately answered follow-up!")
    else:
        print("\n>>> WARNING: Live Aarka stream did not fully recall all facts.")

if __name__ == "__main__":
    test_api()
