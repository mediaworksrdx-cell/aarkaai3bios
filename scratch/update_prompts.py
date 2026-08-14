import sys

filepath = "modules/aarkaa_engine.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

target = '                    "Coding:\\n"\n                    "- Explain code accurately.\\n"\n                    "- Detect bugs and logical errors.\\n"\n                    "- Provide correct complexity analysis.\\n"\n                    "- Understand algorithms, data structures, databases, APIs, Python, JavaScript, Java, Kotlin, SQL, and system design concepts.\\n"\n                    "- Ensure outputs match the code logic.\\n\\n"\n                    "Reasoning:\\n"\n                    "- Solve mathematical and logical problems carefully.\\n"\n                    "- Detect trick questions and false assumptions.\\n"\n                    "- Show calculations when needed.\\n"\n                    "- For impossible scenarios, explain why they are impossible.\\n\\n"'

replacement = '                    "Coding:\\n"\n                    "- No Toy Architectures or Placeholders: When asked to implement complex data structures (including B/B+ trees, AVL/Red-Black trees, heap structures, priority queues, segment trees, and graph algorithms), the code must be fully functional, compiling/interpreting, and compliant with textbook definitions.\\n"\n                    "- Mandatory Balance and Recursion: For tree structures, write complete recursive split, merge, rotation, or balance mechanics. Basic insertion loops without restructuring elements are forbidden.\\n"\n                    "- Safety and Edge Handling: Explicitly check bounds, array allocation size limits, duplicate keys, null/empty parameters, and correctly link adjacent leaves (e.g., leaf next/prev chains in B+ trees).\\n"\n                    "- Ensure outputs match code logic and do not contain placeholder comments.\\n\\n"\n                    "Reasoning:\\n"\n                    "- Solve mathematical and logical problems carefully.\\n"\n                    "- Detect trick questions and false assumptions.\\n"\n                    "- Show calculations when needed.\\n"\n                    "- For impossible scenarios, explain why they are impossible.\\n\\n"'

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Success: Prompt successfully updated.")
else:
    # Try looking for a simplified substring to replace
    sub_target = '                    "Coding:\\n"\n                    "- Explain code accurately.\\n"\n                    "- Detect bugs and logical errors.\\n"\n                    "- Provide correct complexity analysis.\\n"\n                    "- Understand algorithms, data structures, databases, APIs, Python, JavaScript, Java, Kotlin, SQL, and system design concepts.\\n"\n                    "- Ensure outputs match the code logic.\\n\\n"'
    sub_replacement = '                    "Coding:\\n"\n                    "- No Toy Architectures or Placeholders: When asked to implement complex data structures (including B/B+ trees, AVL/Red-Black trees, heap structures, priority queues, segment trees, and graph algorithms), the code must be fully functional, compiling/interpreting, and compliant with textbook definitions.\\n"\n                    "- Mandatory Balance and Recursion: For tree structures, write complete recursive split, merge, rotation, or balance mechanics. Basic insertion loops without restructuring elements are forbidden.\\n"\n                    "- Safety and Edge Handling: Explicitly check bounds, array allocation size limits, duplicate keys, null/empty parameters, and correctly link adjacent leaves (e.g., leaf next/prev chains in B+ trees).\\n"\n                    "- Ensure outputs match code logic and do not contain placeholder comments.\\n\\n"'
    if sub_target in content:
        content = content.replace(sub_target, sub_replacement)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print("Success: Prompt successfully updated via sub-target.")
    else:
        print("Error: Target not found.")
