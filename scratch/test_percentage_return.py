import uuid
from pipeline import process_query
from modules import aarkaa_engine

print("Initializing local engine...")
aarkaa_engine.init()

query = "A stock falls 75%. What percentage gain is needed to return to the original price?"
print(f"Query: {query}")

session_id = str(uuid.uuid4())
res = process_query(query, session_id=session_id, mode="production")

print("\n--- Response ---")
print("Intent detected:", res.intent)
print("Sources used:", res.sources)
print("Answer:")
print(res.response)
