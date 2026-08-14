import sys
import os
sys.path.append(os.getcwd())

import modules.aarkaa_engine as ae
import logging

logging.basicConfig(level=logging.INFO)

print("Initializing engine...")
ae.init()

query = """13. Design an AI image generation service.

Explain:
- GPU scheduling
- Queueing
- Cost optimization
- Multi-user isolation"""

print("Running primary_check...")
resp, conf = ae.primary_check(query)
print("\n=== CLEANED RESPONSE ===")
print(resp)
print("=== END CLEANED RESPONSE ===\n")

print("Let's see what happens if we generate raw response (without clean_response)...")
# Let's bypass _clean_response by doing it ourselves
system_prompt = (
    "You are AARKAA, a helpful and precise AI assistant. "
    "You cannot predict the future price of financial products or speculative assets (stocks, cryptocurrencies, commodities, etc.). "
    "If the user asks for a future price prediction or forecast, you must politely decline, explaining that future market behavior is speculative and unpredictable."
)
user_prompt = f"Answer the following question: {query}\n\n"
prompt = ae._build_chatml(system_prompt, user_prompt)
tokens = ae.MAX_TOKENS
temp = ae._get_temperature(query, "general_query")

# Call _generate_stream directly
print("\n=== RAW STREAMING RESPONSE ===")
for tok in ae._generate_stream(prompt, max_new_tokens=tokens, temperature=temp):
    print(tok, end="", flush=True)
print("\n=== END RAW RESPONSE ===\n")
