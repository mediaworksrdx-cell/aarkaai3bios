import os

with open("main.py", "r", encoding="utf-8") as f:
    content = f.read()

target = "    finally:\n        session.close()\n\n\n# ─── Screener API Endpoints"

replacement = """    finally:
        session.close()


@app.get("/admin/encyclopedia", response_class=fastapi.responses.HTMLResponse, tags=["admin"])
def admin_get_encyclopedia():
    \"\"\"Get standalone interactive 240-query technical encyclopedia viewer.\"\"\"
    viewer_path = os.path.join(os.path.dirname(__file__), "audit_240_viewer.html")
    if os.path.exists(viewer_path):
        with open(viewer_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Encyclopedia viewer not found</h1>"


@app.get("/admin/encyclopedia/json", tags=["admin"])
def admin_get_encyclopedia_json():
    \"\"\"Get raw JSON of all 240 queries and verified answers.\"\"\"
    json_path = os.path.join(os.path.dirname(__file__), "agent_240_full_queries_and_answers.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"error": "Encyclopedia JSON not found"}


# ─── Screener API Endpoints"""

if target in content:
    content = content.replace(target, replacement, 1)
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated main.py successfully!")
else:
    # try CRLF
    target_crlf = target.replace("\n", "\r\n")
    replacement_crlf = replacement.replace("\n", "\r\n")
    if target_crlf in content:
        content = content.replace(target_crlf, replacement_crlf, 1)
        with open("main.py", "w", encoding="utf-8") as f:
            f.write(content)
        print("Updated main.py (CRLF) successfully!")
    else:
        print("Target not found!")
