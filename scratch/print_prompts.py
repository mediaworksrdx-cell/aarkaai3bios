import sys
sys.path.append("/home/ubuntu/aarkaai3b")

import re
import modules.aarkaa_engine as engine

engine.init()

query = "You have 8 balls. One is heavier. Find it in 2 weighings."

# 1. From test_different_prompts.py (Option 3)
dummy_prompt, _, _ = engine._build_final_prompt(query, "", "reasoning_puzzle", "en", "production")
system_prompt_match = re.search(r"<\|im_start\|>system\n(.*?)<\|im_end\|>", dummy_prompt, re.DOTALL)
system_prompt = system_prompt_match.group(1)
user_inst = "Apply the 'Scale Weighing Puzzles' rule to solve the question. You must use the exact logical cases (Case 1, Case 2, Case 3) and wording from the example in the rules, but adapted to this question. Do NOT assign numbers, letters, or names to individual items."
user_prompt_opt3 = f"Question: {query}\n\nTo solve this puzzle, follow these instructions strictly:\n{user_inst}"
prompt_opt3 = engine._build_chatml(system_prompt, user_prompt_opt3)

# 2. From final_response
prompt_final_response, _, _ = engine._build_final_prompt(query, "", "reasoning_puzzle")

print("Prompt Option 3 Length:", len(prompt_opt3))
print("Prompt final_response Length:", len(prompt_final_response))
print("Are they identical?", prompt_opt3 == prompt_final_response)

if prompt_opt3 != prompt_final_response:
    # Print diff or highlight differences
    print("\n--- DIFF ---")
    import difflib
    diff = difflib.unified_diff(
        prompt_opt3.splitlines(keepends=True),
        prompt_final_response.splitlines(keepends=True),
        fromfile="prompt_opt3",
        tofile="prompt_final_response"
    )
    sys.stdout.writelines(diff)
