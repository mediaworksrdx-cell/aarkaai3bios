from modules import aarkaa_engine

aarkaa_engine.init()

print("\n--- Testing primary_check ---")
try:
    ans, conf = aarkaa_engine.primary_check("Hello")
    print("primary_check ans:", ans)
except Exception as e:
    print("primary_check error:", e)

print("\n--- Testing final_response without context ---")
try:
    ans2 = aarkaa_engine.final_response("How to write a python list comprehension?", "", intent="coding_help")
    print("final_response ans:", ans2)
except Exception as e:
    print("final_response error:", e)
