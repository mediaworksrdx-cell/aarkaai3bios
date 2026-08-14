import sys

filepath = "modules/agents/debugging.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

target = """            rules=[
                "Analyze stack traces, runtime errors, and output logs with high scrutiny.",
                "Isolate the root cause of failures before proposing code modifications.",
                "Provide clear, corrected code patches showing what was changed and why.",
                "Detail common failure modes or edge cases associated with the bug."
            ],"""

replacement = """            rules=[
                "Analyze stack traces, compiler outputs, runtime errors, and logs with extreme precision.",
                "Verify API constraints, type signatures, pointer definitions, recursion depths, and variables availability.",
                "Confirm the exact invariants of targeted structures (e.g. balance constraints, height adjustments, leaf link pointers) are preserved.",
                "Isolate the root cause of failures and perform a comprehensive logic simulation (dry run) before proposing code modifications.",
                "Ensure no placeholders or partial stubs remain in corrected implementations.",
                "Provide clear, corrected code patches showing what was changed and why, detailing edge cases."
            ],"""

if target in content:
    content = content.replace(target, replacement)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    print("Success: Debugging Agent rules updated.")
else:
    print("Error: Target not found.")
