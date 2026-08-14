import os
tasks_dir = r"C:\Users\daarv\.gemini\antigravity\brain\318e557b-59f2-4cf1-9ab2-62478c0cb35f\.system_generated\tasks"
if os.path.exists(tasks_dir):
    for f in os.listdir(tasks_dir):
        if "94" in f:
            filepath = os.path.join(tasks_dir, f)
            print(f"Reading file: {filepath}")
            with open(filepath, "r", encoding="utf-8", errors="ignore") as file:
                print(file.read()[-1000:])
else:
    print("Tasks dir does not exist")
