import sys
sys.path.append("/home/ubuntu/aarkaai3b")

import modules.aarkaa_engine as engine

engine.init()

query = "You have 8 balls. One is heavier. Find it in 2 weighings."
print("Running final_response for weighing query...")
response = engine.final_response(query, "", "reasoning_puzzle")
print("Response:")
print(response)
