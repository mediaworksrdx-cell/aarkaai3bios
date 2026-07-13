"""
AARKAAI – Topological DAG Execution Engine
Executes task plans, handles tool calls, retries, and updates.
"""
from __future__ import annotations

import logging
from typing import Dict, Any, List

from modules.tools import registry
from modules import supervisor
from modules import task_memory

def check_python_script_safety(command: str) -> tuple[bool, str]:
    """Parse command to check safety of any referenced Python script AST."""
    import ast
    import re
    from pathlib import Path
    
    match = re.search(r'\bpython(?:3)?\s+([a-zA-Z0-9_\-\.\/]+)', command)
    if not match:
        return True, ""
        
    script_name = match.group(1)
    try:
        from modules.tools.fs import _resolve_safe_path
        resolved_path = _resolve_safe_path(script_name)
    except Exception:
        return True, ""
        
    if not resolved_path.is_file():
        return True, ""
        
    try:
        content = resolved_path.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content)
    except Exception as e:
        return False, f"Failed to parse python script AST: {e}"
        
    blocked_imports = {"subprocess", "pty", "shutil"}
    blocked_calls = {"system", "popen", "spawn", "rmtree", "eval", "exec"}
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name in blocked_imports:
                    return False, f"Blocked import: '{alias.name}'"
        elif isinstance(node, ast.ImportFrom):
            if node.module in blocked_imports:
                return False, f"Blocked import from: '{node.module}'"
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in blocked_calls:
                    return False, f"Blocked function attribute call: '{node.func.attr}'"
            elif isinstance(node.func, ast.Name):
                if node.func.id in blocked_calls:
                    return False, f"Blocked function call: '{node.func.id}'"
                    
    return True, ""

logger = logging.getLogger(__name__)

def execute(plan: Dict[str, Any], goal_id: int, user_id: str, session_id: str) -> str:
    """Core topological scheduler executing tasks of a validated DAG."""
    scratchpad = {
        "facts": [],
        "assumptions": [],
        "unknowns": [],
        "evidence": {}
    }
    
    super_inst = supervisor.Supervisor()
    tasks = plan.get("tasks", [])
    
    # Simple topological sorting
    executed = {} # id -> result_summary
    
    # Flag to monitor if we hit an approval gate block
    paused_for_approval = False
    
    while len(executed) < len(tasks):
        # Find next runnable task (all deps satisfied)
        runnable = None
        for t in tasks:
            if t["id"] in executed:
                continue
            deps = t.get("dependencies", [])
            if all(dep in executed for dep in deps):
                runnable = t
                break
                
        if not runnable:
            logger.error("No runnable tasks found. Cycle check failed or tasks orphaned.")
            break
            
        task_id = runnable["id"]
        
        # Check human approval gate requirements
        if runnable.get("approval_required", False) and runnable.get("status") == "pending":
            logger.info("Task %s requires human approval. Pausing execution.", task_id)
            runnable["status"] = "paused"
            task_memory.update_goal_state(goal_id, plan, scratchpad, "paused")
            paused_for_approval = True
            break
            
        tool_name = runnable.get("tool_hint")
        logger.info("Executing subtask %s using %s", task_id, tool_name)
        
        # Verify loops using supervisor
        params = {"query": runnable.get("description", "")}
        if tool_name and super_inst.check_loop(task_id, tool_name, params):
            runnable["status"] = "failed"
            task_memory.update_goal_state(goal_id, plan, scratchpad, "failed")
            return f"Supervisor interrupted execution loop on subtask: {runnable['name']}."
            
        # Try execution
        runnable["status"] = "running"
        task_memory.update_goal_state(goal_id, plan, scratchpad, "running")
        
        result = ""
        success = False
        retry_budget = runnable.get("retry_budget", 2)
        
        for attempt in range(retry_budget + 1):
            try:
                if not tool_name:
                    # Fallback default text generation if tool is not required
                    from modules import aarkaa_engine
                    result = aarkaa_engine.generate_raw(runnable["description"], max_new_tokens=512)
                    success = True
                    break
                
                # Perform tool call
                tool_params = {}
                if tool_name == "WebSearch":
                    tool_params = {"query": runnable["description"]}
                elif tool_name == "FileEditTool":
                    # Parse simplified mock content for fallback testing
                    tool_params = {"path": "strategic_findings.txt", "content": runnable["description"]}
                elif tool_name == "FileReadTool":
                    tool_params = {"path": "strategic_findings.txt"}
                else:
                    tool_params = {"command": runnable["description"]}
                
                # Dynamic Permission Gate Verification
                from modules.permissions import verify_permission, PermissionLevel
                from modules.audit_log import log_audit_event
                perm_level, perm_msg = verify_permission(tool_name, tool_params)
                
                # Check nested script safety if BashTool executes python script
                if tool_name == "BashTool" and perm_level != PermissionLevel.STRICT_BLOCK:
                    script_ok, script_msg = check_python_script_safety(tool_params.get("command", ""))
                    if not script_ok:
                        perm_level = PermissionLevel.STRICT_BLOCK
                        perm_msg = f"Script analysis blocked: {script_msg}"

                if perm_level == PermissionLevel.STRICT_BLOCK:
                    result = f"Error: Command blocked by safety layer. {perm_msg}"
                    logger.error("Blocked command execution: %s for %s", tool_params, tool_name)
                    log_audit_event(user_id, session_id, tool_name, tool_params, perm_level, "BLOCKED", perm_msg)
                    success = False
                    break
                elif perm_level == PermissionLevel.USER_CONFIRM:
                    import sys
                    if sys.stdin.isatty():
                        confirm_input = input(f"⚠️ AARKAAI Security Gate: {perm_msg}. Proceed? (y/n): ")
                        if confirm_input.strip().lower() not in ["y", "yes"]:
                            result = "Error: Command aborted by user confirmation reject."
                            logger.info("User rejected execution of: %s", tool_name)
                            log_audit_event(user_id, session_id, tool_name, tool_params, perm_level, "REJECTED", "User declined interactive prompt.")
                            success = False
                            break
                        else:
                            log_audit_event(user_id, session_id, tool_name, tool_params, perm_level, "ALLOWED_BY_USER", "User approved interactive prompt.")
                    else:
                        logger.warning("Running USER_CONFIRM action in headless context: %s %s", tool_name, tool_params)
                        log_audit_event(user_id, session_id, tool_name, tool_params, perm_level, "ALLOWED_BY_DEFAULT", "Headless context auto-approved.")
                else:
                    log_audit_event(user_id, session_id, tool_name, tool_params, perm_level, "ALLOWED", "Safe read execution.")

                result = registry.execute_tool(tool_name, tool_params)
                log_audit_event(user_id, session_id, tool_name, tool_params, perm_level, "EXECUTED", f"Exit status or length: {len(result)}")
                
                if "Error" not in result:
                    success = True
                    break
                else:
                    raise ValueError(result)
            except Exception as e:
                logger.warning("Attempt %d failed for subtask %s: %s", attempt + 1, task_id, e)
                if attempt < retry_budget:
                    super_inst.record_retry()
                    if not super_inst.check_retry_budget():
                        break
                        
        if success:
            runnable["status"] = "completed"
            executed[task_id] = result
            # Add to working memory context
            scratchpad["evidence"][task_id] = result
            scratchpad["facts"].append(f"Task {task_id} complete: {runnable['name']}")
        else:
            runnable["status"] = "failed"
            task_memory.update_goal_state(goal_id, plan, scratchpad, "failed")
            return f"Execution aborted. Subtask failed: {runnable['name']}. Detail: {result}"
            
        task_memory.update_goal_state(goal_id, plan, scratchpad, "running")

    if paused_for_approval:
        return "Execution paused waiting for human approval gate."
        
    task_memory.update_goal_state(goal_id, plan, scratchpad, "completed")
    
    # Combine results for final compilation
    from modules import aarkaa_engine
    compilation_prompt = f"Consolidate the completed tasks execution results to present a cohesive answer for query: '{plan.get('goal')}'\n\nResults:\n"
    for tid, res in executed.items():
        compilation_prompt += f"### Task {tid}:\n{res}\n\n"
        
    final_output = aarkaa_engine.generate_raw(compilation_prompt, max_new_tokens=1024)
    return final_output
