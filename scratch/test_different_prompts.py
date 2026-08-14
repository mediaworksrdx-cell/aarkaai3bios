import sys
sys.path.append("/home/ubuntu/aarkaai3b")

import re
import modules.aarkaa_engine as engine

engine.init()

query = "You have 8 balls. One is heavier. Find it in 2 weighings."

# Extract system prompt
dummy_prompt, _, _ = engine._build_final_prompt(query, "", "reasoning_puzzle", "en", "production")
system_prompt_match = re.search(r"<\|im_start\|>system\n(.*?)<\|im_end\|>", dummy_prompt, re.DOTALL)
if system_prompt_match:
    system_prompt = system_prompt_match.group(1)
else:
    print("Failed to extract system prompt!")
    sys.exit(1)

# We will try different prompt formulations for the weighing puzzle
prompts = [
    # Option 1: Emphasize copying the system rules structure and forbidding listing/naming
    (
        "1. Identify and state the applicable category from the reference rules above.\n"
        "2. Divide the items into Group A, Group B, and Group C, stating the number of items in each group. Do NOT list the items or write curly braces '{}'.\n"
        "3. Detail the cases for Weighing 1 and Weighing 2 by adapting the exact wording and structure of the 'Scale Weighing Puzzles' example above. Do NOT use numbers, letters, or names (e.g. 'Ball 1', 'Coin A') for individual items; refer to them only as 'Group A items', 'Group B items', 'Group C items', or 'the unweighed item'.\n"
        "4. State the final solution clearly and concisely."
    ),
    # Option 2: Short, highly direct step-by-step
    (
        "1. Identify the applicable category: Scale Weighing Puzzles.\n"
        "2. Divide the 8 balls into Group A (3), Group B (3), and Group C (2). Do NOT assign names or numbers like 'Ball 1' to individual balls.\n"
        "3. Describe Weighing 1 (weighing Group A against Group B).\n"
        "4. Describe Weighing 2 for the case where they balance (weighing the 2 balls in Group C against each other).\n"
        "5. Describe Weighing 2 for the case where Group A is heavier (weighing 2 balls from Group A against each other, leaving the 3rd unweighed).\n"
        "6. Describe Weighing 2 for the case where Group B is heavier (weighing 2 balls from Group B against each other, leaving the 3rd unweighed).\n"
        "7. State the final solution clearly and concisely."
    ),
    # Option 3: Very simple, forcing the model to only use the system prompt wording
    (
        "Apply the 'Scale Weighing Puzzles' rule to solve the question. You must use the exact logical cases (Case 1, Case 2, Case 3) and wording from the example in the rules, but adapted to this question. Do NOT assign numbers, letters, or names to individual items."
    )
]

for i, user_inst in enumerate(prompts):
    print(f"\n========================================")
    print(f"PROMPT OPTION {i+1}:")
    print(f"========================================")
    
    user_prompt = f"Question: {query}\n\nTo solve this puzzle, follow these instructions strictly:\n{user_inst}"
    prompt = engine._build_chatml(system_prompt, user_prompt)
    
    print("Running generation...")
    # Using temperature 0.0 for logic reasoning
    stop_tokens = ["<|im_end|>", "<|im_start|>", "<|endoftext|>"]
    stream = engine._model(
        prompt,
        max_tokens=1500,
        temperature=0.0,
        stop=stop_tokens,
        stream=True
    )
    
    tokens = []
    for chunk in stream:
        token = chunk["choices"][0]["text"]
        if token:
            print(token, end="", flush=True)
            tokens.append(token)
    print()
