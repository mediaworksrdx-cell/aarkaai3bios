import sys
import os

# Adjust path to import modules correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from modules.web_search import get_web_context

def main():
    print("Testing web search authority sorting and filtering...")
    query = "engineering colleges in Tamil Nadu 2026"
    print(f"Query: {query}\n")
    
    context = get_web_context(query, max_results=5)
    print("--- Web Context Result ---")
    print(context)
    print("--------------------------")

if __name__ == "__main__":
    main()
