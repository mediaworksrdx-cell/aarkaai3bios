import sys

filepath = "modules/agents/coding.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

target = """            rules=[
                "Write production-grade, cleanly formatted code.",
                "Always explain code logic, complex algorithms, or syntax decisions.",
                "Use clear Markdown code blocks specifying the programming language (e.g., ```python).",
                "Focus on efficiency, error handling, performance optimization, and dry-run code logic."
            ],"""

replacement = """            rules=[
                "Write production-grade, cleanly formatted code adhering strictly to textbook specifications and operational algorithms (e.g. B/B+ trees, AVL/Red-Black trees, heap structures).",
                "No Non-functional Stubs or Placeholders: Implementing simplified logic without recursive splitting, tree balancing, or edge constraints is strictly forbidden.",
                "For tree structures, always implement complete recursive split, merge, borrow, or balance mechanics.",
                "Strict Safety checks: Audit array boundaries, duplicate keys, null/empty parameters, and sibling pointer structures (e.g. leaf next/prev chains in B+ trees).",
                "Focus on efficiency, memory safety, error handling, and performance optimization.",
                "Detail common failure modes or edge cases associated with the code."
            ],"""

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Success: Coding Agent rules updated.")
else:
    print("Error: Target not found.")
