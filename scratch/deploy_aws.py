import os
import zipfile
import subprocess
import time

# ─── Configuration ────────────────────────────────────────────────────────────
PEM_KEY = r"C:\Users\daarv\Downloads\aarkaai3b.pem"
HOST = "16.170.206.243"
PORT = 22
USER = "ec2-user"
REMOTE_DIR = "/workspace/aarkaai3b"
ZIP_NAME = "aarkaai_update.zip"

# Read from scratch/deploy.py to use same list of files
FILES_TO_PACK = [
    "config.py",
    "database.py",
    "main.py",
    "pipeline.py",
    "register_visitor.py",
    "schemas.py",
    "generate_market_research_report.py",
    "generate_chennai_startups.py",
    "modules/__init__.py",
    "modules/aarkaa_engine.py",
    "modules/auth.py",
    "modules/auto_learn.py",
    "modules/finance.py",
    "modules/memory.py",
    "modules/options_strategy.py",
    "modules/subscription.py",
    "modules/technical.py",
    "modules/web_search.py",
    "modules/semantic_filter.py",
    "modules/rag.py",
    "modules/coordinator.py",
    "modules/gamma_pdf.py",
    "modules/gamma_charts.py",
    "modules/tools/__init__.py",
    "modules/tools/base.py",
    "modules/tools/bash.py",
    "modules/tools/fs.py",
    "modules/tools/skill_tools.py",
    "modules/tools/web.py",
    "modules/tools/image.py",
    "modules/goal_planner.py",
    "modules/supervisor.py",
    "modules/task_memory.py",
    "modules/execution_engine.py",
    "modules/reflection.py",
    "modules/agents/__init__.py",
    "modules/agents/base.py",
    "modules/agents/coding.py",
    "modules/agents/debugging.py",
    "modules/agents/finance.py",
    "modules/agents/trading.py",
    "modules/agents/marketing.py",
    "modules/agents/research.py",
    "modules/agents/support.py",
    "modules/agents/router.py",
    "modules/agents/verifier.py",
    "middleware.py",
    "skills/__init__.py",
    "skills/skill_registry.py",
    "skills/pdf/SKILL.md",
    "skills/pdf/docs_generator.py",
    "skills/docx/SKILL.md",
    "skills/xlsx/SKILL.md",
    "skills/pptx/SKILL.md",
    "skills/file-reading/SKILL.md",
    "skills/frontend-design/SKILL.md",
    "skills/skill-router/SKILL.md",
    "skills/skill-router/skill_registry.py",
    "skills/html/SKILL.md",
    "skills/html/docs_generator.py",
    "skills/premium-report/SKILL.md",
    "skills/skill-creator/SKILL.md",
    "skills/gamma-chart/SKILL.md",
    "skills/gamma-pdf/SKILL.md",
    "scratch/remote_db_migrate.py",
    "scratch/test_compilation_direct.py",
    "scratch/check_pdf_details.py",
    "scratch/test_base64.py",
    "scratch/read_chats.py",
    "scratch/migrate_to_chromadb.py",
    "scratch/run_local_test.py",
    "scratch/test_remote_invoice.py",
    "scratch/test_remote_dynamic_naming.py",
    "scratch/test_remote_html_render.py",
    "scratch/test_memory_retention.py",
    "scratch/verify_cpu_idle.py",
    "requirements.txt",
    "remote_deploy.sh",
    "merge_lora.py",
]

# ─── Step 1: Package Files into ZIP ──────────────────────────────────────────
print("Step 1: Packaging updated files...")
with zipfile.ZipFile(ZIP_NAME, "w", zipfile.ZIP_DEFLATED) as zipf:
    # Add files from FILES_TO_PACK (skipping hardcoded skills/ paths to pack dynamically instead)
    for file_path in FILES_TO_PACK:
        if file_path.startswith("skills/"):
            continue
        if os.path.exists(file_path):
            zipf.write(file_path)
            print(f"  Added {file_path}")
        else:
            print(f"  Warning: File {file_path} not found!")
            
    # Dynamically pack the entire skills folder
    print("  Dynamically packaging the skills directory...")
    for root, dirs, files in os.walk("skills"):
        if "__pycache__" in root or "user-skills" in root:
            continue
        for file in files:
            full_path = os.path.join(root, file)
            # Use relative path for the zip archive
            zipf.write(full_path)
            print(f"  Added dynamic skill file: {full_path}")

print("Packaging complete.")

# ─── Step 1.5: Create Remote Directory ───────────────────────────────────────
print("\nStep 1.5: Creating remote directory if it doesn't exist...")
mkdir_cmd = [
    "ssh",
    "-p", str(PORT),
    "-i", PEM_KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    f"{USER}@{HOST}",
    f"mkdir -p {REMOTE_DIR}"
]
print("Running command:", " ".join(mkdir_cmd))
subprocess.run(mkdir_cmd, capture_output=True, text=True)

# ─── Step 2: Upload via SCP ──────────────────────────────────────────────────
print("\nStep 2: Uploading ZIP to remote server...")
scp_cmd = [
    "scp",
    "-P", str(PORT),
    "-i", PEM_KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    ZIP_NAME,
    f"{USER}@{HOST}:{REMOTE_DIR}/"
]

print("Running command:", " ".join(scp_cmd))
result = subprocess.run(scp_cmd, capture_output=True, text=True, encoding="utf-8")
if result.returncode != 0:
    print(f"SCP failed: {result.stderr}")
    exit(1)
print("Upload successful.")

# Remove local zip
if os.path.exists(ZIP_NAME):
    os.remove(ZIP_NAME)

# ─── Step 3: Run Remote SSH Deployment Commands ─────────────────────────────
print("\nStep 3: Executing remote deployment commands via SSH...")

remote_commands = f"cd {REMOTE_DIR} && unzip -o {ZIP_NAME} remote_deploy.sh && bash remote_deploy.sh && rm -f remote_deploy.sh"

ssh_cmd = [
    "ssh",
    "-p", str(PORT),
    "-i", PEM_KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    f"{USER}@{HOST}",
    remote_commands
]

print("Running SSH commands...")
result = subprocess.run(ssh_cmd, capture_output=True, text=True, encoding="utf-8")
print("SSH Command Output:")
print(result.stdout.encode('ascii', 'ignore').decode('ascii'))
print(f"SSH return code: {result.returncode}")
if result.returncode != 0:
    print(f"SSH failed (code {result.returncode}): {result.stderr.encode('ascii', 'ignore').decode('ascii')}")
    if "Started aarkaai in background" not in result.stdout:
        exit(1)

# ─── Step 4: Verify Deployment ───────────────────────────────────────────────
print("\nStep 4: Verifying remote deployment health check internally...")

time.sleep(5)

verify_cmd = [
    "ssh",
    "-p", str(PORT),
    "-i", PEM_KEY,
    "-o", "StrictHostKeyChecking=no",
    "-o", "BatchMode=yes",
    f"{USER}@{HOST}",
    "curl -s http://localhost:5000/health"
]

for attempt in range(8):
    try:
        print(f"Attempt {attempt+1}: Querying remote health check...")
        res = subprocess.run(verify_cmd, capture_output=True, text=True, encoding="utf-8")
        if res.returncode == 0 and ("200" in res.stdout or '"status"' in res.stdout):
            print("Deployment verified successfully! Remote health check returned 200/status.")
            print(res.stdout)
            break
        else:
            print(f"Health check failed or pending. Output: {res.stdout.strip()} Error: {res.stderr.strip()}")
    except Exception as e:
        print(f"Attempt {attempt+1} exception: {e}")
    time.sleep(4)
else:
    print("Health check could not be verified after 8 attempts.")
