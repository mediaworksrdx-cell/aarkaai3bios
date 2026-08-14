import sys
import os

# Adjust path to find the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline import _detect_requested_language
from modules.aarkaa_engine import _build_final_prompt

def run_test():
    test_cases = [
        {
            "query": "Translate to Samanantar Hindi: The climate is changing rapidly.",
            "expected_lang": "hi",
            "alignment_name": "Samanantar Hindi"
        },
        {
            "query": "Respond in Tamil Alpaca: Explain neural networks in simple terms.",
            "expected_lang": "ta",
            "alignment_name": "Tamil Alpaca"
        },
        {
            "query": "Answer using Aya: How does photosynthesis work?",
            "expected_lang": "hi", # Aya defaults to Hindi
            "alignment_name": "Aya (Indian Languages)"
        },
        {
            "query": "Translate to Tamil using Aya: Welcome to our platform.",
            "expected_lang": "ta", # Aya with Tamil keyword
            "alignment_name": "Aya (Indian Languages)"
        },
        {
            "query": "Write a story in Hindi Alpaca about a farmer.",
            "expected_lang": "hi",
            "alignment_name": "Hindi Alpaca"
        }
    ]

    for idx, tc in enumerate(test_cases):
        print(f"\n--- Test Case {idx+1}: {tc['query']} ---")
        # Detect language
        detected_lang = _detect_requested_language(tc["query"], "en")
        print(f"Detected Lang: {detected_lang} (Expected: {tc['expected_lang']})")
        
        # Build prompt
        prompt, tokens, temp = _build_final_prompt(tc["query"], context="", intent="general_query", lang=detected_lang)
        
        # Verify alignment instruction is present in system block of ChatML
        # Standard system block has alignment instructions appended.
        has_alignment = tc["alignment_name"] in prompt
        print(f"Has Alignment Prompt Info: {has_alignment}")
        if not has_alignment:
            print("WARNING: Alignment prompt not found in built prompt!")
            print(prompt[:400])

if __name__ == "__main__":
    run_test()
