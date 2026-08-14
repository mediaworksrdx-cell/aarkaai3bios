import os

file_path = os.path.join("modules", "aarkaa_engine.py")

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace hardcoded tokens = 3800 with tokens = MAX_TOKENS
new_content = content.replace("tokens = 3800", "tokens = MAX_TOKENS")

# Verify replacements
replaced_count = content.count("tokens = 3800")
print(f"Occurrences found: {replaced_count}")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(new_content)

print("Replacement complete.")
