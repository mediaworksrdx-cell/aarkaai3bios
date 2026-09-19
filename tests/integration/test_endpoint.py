import requests

if __name__ == "__main__":
    try:
        resp = requests.post("http://localhost:5000/prompt", json={"query": "Hello?", "user_id": "test"}, timeout=5)
        print("HELLO QUERY:")
        print("Status:", resp.status_code)
        try:
            print("JSON:", resp.json())
        except Exception as e:
            print("TEXT:", resp.text)
    except Exception as e:
        print(e)

