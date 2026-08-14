from modules.architecture_verifier import is_architecture_query, verify_architecture_response

query = "design a url shortening service"
response = """### URL Shortening Service Architecture ...""" # (truncated or full)

print("Is architecture query:", is_architecture_query(query))
