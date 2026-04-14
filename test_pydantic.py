import json
from schemas import PromptRequest

try:
    data = {"prompt": "What is EBITDA", "user_id": "rthshr"}
    req = PromptRequest(**data)
    print("SUCCESS:", req)
except Exception as e:
    print("VALIDATION ERROR:", e)
