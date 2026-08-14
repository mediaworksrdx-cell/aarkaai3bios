import sys

filepath = "modules/agents/verifier.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Let's search using a smaller substring target to be safe
target = '2. Coding/Debugging Audit: Check that code blocks are properly formatted and closed, contain valid syntax, do not contain placeholders'

replacement = '2. Coding/Debugging Audit: Check that code blocks are properly formatted and closed, contain valid syntax, do not contain placeholders (like \'// insert code here\'), and use correct parameters. For compiled languages (such as C/C++), strictly verify pointer arithmetic, struct member definitions, type safety, memory allocations (e.g. check malloc returns, buffer sizes, string terminations), and B+ tree node splits logic. Correct any syntax errors directly.'

if target in content:
    # Find the line that starts with 16: and replace it
    lines = content.split("\n")
    for idx, line in enumerate(lines):
        if "2. Coding/Debugging Audit:" in line:
            lines[idx] = '16: ' + replacement
            break
    content = "\n".join(lines)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Success: Verifier SYSTEM_VERIFIER_PROMPT rule 2 updated.")
else:
    # Try literal lookup without line prefix numbering (since git checkout restored original file)
    literal_target = '2. Coding/Debugging Audit: Check that code blocks are properly formatted and closed, contain valid syntax, do not contain placeholders (like \'// insert code here\'), and use correct parameters.'
    if literal_target in content:
        content = content.replace(literal_target, replacement)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print("Success: Verifier SYSTEM_VERIFIER_PROMPT rule 2 updated via literal match.")
    else:
        print("Error: Target not found in file.")
