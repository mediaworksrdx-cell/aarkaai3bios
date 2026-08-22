from pipeline import process_query
print("Testing normal query...")
try:
    res = process_query("Hello there")
    print("Normal result:", res.response)
except Exception as e:
    print("Error:", e)

print("\nTesting coding query...")
try:
    res2 = process_query("write a python script to calculate fibonacci")
    print("Code result:", res2.response)
except Exception as e:
    print("Error:", e)
