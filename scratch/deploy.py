import os
import zipfile
import subprocess
import time
import requests

# ─── Configuration ────────────────────────────────────────────────────────────
PEM_KEY = r"C:\Users\daarv\Downloads\aarkaai3b.pem"
HOST = "16.170.206.243"
PORT = 22
USER = "ec2-user"
REMOTE_DIR = "/workspace/aarkaai3b"
ZIP_NAME = "aarkaai_update.zip"

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
    "modules/cvr_pipeline.py",
    "modules/repair_agents.py",
    "modules/repo_indexer.py",
    "modules/gamma_domains.py",
    "modules/gamma_charts.py",
    "modules/tools/__init__.py",
    "modules/tools/base.py",
    "modules/tools/bash.py",
    "modules/tools/fs.py",
    "modules/tools/git_tool.py",
    "modules/tools/ast_tool.py",
    "modules/tools/memory_tool.py",
    "modules/tools/lsp_tool.py",
    "modules/tools/search_tool.py",
    "modules/tools/file_tool.py",
    "modules/tools/build_tool.py",
    "modules/tools/test_tool.py",
    "modules/tools/deploy_tool.py",
    "modules/tools/security_tool.py",
    "modules/tools/coverage_tool.py",
    "modules/tools/profiler_tool.py",
    "modules/tools/planner_tool.py",
    "modules/tools/linter_tool.py",
    "modules/tools/formatter_tool.py",
    "modules/tools/debugger_tool.py",
    "modules/tools/patch_tool.py",
    "modules/tools/snapshot_tool.py",
    "modules/tools/health_tool.py",
    "modules/tools/rag_tool.py",
    "modules/tools/verifier_tool.py",
    "modules/tools/repair_tool.py",
    "modules/tools/monitor_tool.py",
    "modules/tools/symbol_tool.py",
    "modules/tools/xref_tool.py",
    "modules/tools/call_graph_tool.py",
    "modules/tools/dependency_tool.py",
    "modules/tools/docker_tool.py",
    "modules/tools/db_migrate_tool.py",
    "modules/tools/pkg_manager_tool.py",
    "modules/tools/browser_tool.py",
    "modules/tools/cicd_tool.py",
    "modules/tools/benchmark_tool.py",
    "modules/tools/code_review_tool.py",
    "modules/tools/doc_gen_tool.py",
    "modules/tools/coordinator_tool.py",
    "modules/tools/confidence_tool.py",
    "modules/tools/human_input.py",
    "modules/tools/skill_tools.py",
    "modules/tools/web.py",
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
    "scratch/remote_db_migrate.py",
    "scratch/migrate_to_chromadb.py",
    "scratch/run_local_test.py",
    "scratch/test_remote_invoice.py",
    "scratch/test_remote_dynamic_naming.py",
    "scratch/test_remote_html_render.py",
    "scratch/test_memory_retention.py",
    "scratch/verify_cpu_idle.py",
    "scratch/insert_expert_sysdesign.py",
    "scratch/run_remote_verify.py",
    "scratch/trigger_remote_test.py",
    "requirements.txt",
    "remote_deploy.sh",
    "migrate_add_role.py",
    "nginx_site.conf",
    "nginx_timeout.conf",
    "FinGenIQ_route.ts",
    ".env.production.template",
]



# ─── Step 1: Package Files into ZIP ──────────────────────────────────────────
print("Step 1: Packaging updated files...")
with zipfile.ZipFile(ZIP_NAME, "w", zipfile.ZIP_DEFLATED) as zipf:
    for file_path in FILES_TO_PACK:
        if os.path.exists(file_path):
            zipf.write(file_path)
            print(f"  Added {file_path}")
        else:
            print(f"  Warning: File {file_path} not found!")

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
    # Don't fail the script if backend started and returned code 130 or 255 due to SSH channel close/timeout/etc.
    if "Started aarkaai in background" not in result.stdout:
        exit(1)


# ─── Step 4: Verify Deployment ───────────────────────────────────────────────
print("\nStep 4: Verifying remote deployment health check internally...")

# Wait a few seconds for LLM/models to load
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
        if res.returncode == 0 and "200" in res.stdout or '"status"' in res.stdout:
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

