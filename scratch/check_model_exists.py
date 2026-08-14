import requests

model_id = "rthshr/aarkaa-3b"
url = f"https://huggingface.co/api/models/{model_id}"
res = requests.get(url)
print("Status Code:", res.status_code)
if res.status_code == 200:
    print("Model found!")
    print(res.json())
else:
    print("Model not found or private. Response:")
    print(res.text)
