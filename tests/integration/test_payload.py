from pipeline import process_query

print("Testing user payload:")
try:
    res = process_query("What is EBITDA and why is it important", "rthshr")
    print("Code result:", res.response)
except Exception as e:
    import traceback
    traceback.print_exc()
