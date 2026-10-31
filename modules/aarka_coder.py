"""
AARKAAI – Aarka Coder Pipeline

Dual-model code generation pipeline:
  1. Coder 3B model generates raw code
  2. CVR pipeline validates syntax + security
  3. Coder 3B auto-generates unit tests
  4. Sandbox executes code + tests
  5. Returns structured result for 7B polish pass
"""
from __future__ import annotations

import logging
import re
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def generate_code(query: str, context: str = "", language: str = "python") -> str:
    """
    Generate production-grade code adhering strictly to specifications.
    Uses AARKAA inference with automatic markdown code extraction.
    """
    from modules import aarkaa_engine
    
    system_prompt = (
        "You are Aarka Coder, an expert quantitative software architect and systems engineer. "
        "Generate clean, robust, and mathematically exact code adhering strictly to specifications. "
        "Include type hints, docstrings, and comprehensive error handling. "
        "Output production-grade, executable code inside a single markdown code block. "
        "FORBIDDEN: Do not output package installation commands such as 'pip install'. Always write pure Python implementation code."
    )
    
    user_prompt = f"{query}\n\nContext:\n{context}" if context else query
    prompt = aarkaa_engine._build_chatml(system_prompt, user_prompt)
    
    try:
        raw = aarkaa_engine._generate(
            prompt,
            max_new_tokens=2048,
            temperature=0.2,
            force_general=True
        )
        blocks = extract_code_blocks(raw)
        code_out = blocks[0]["code"] if (blocks and blocks[0].get("code")) else raw.strip()
        code_out = "\n".join(l for l in code_out.splitlines() if not l.strip().startswith(("pip ", "npm ", "$ "))).strip()
        if not code_out or len(code_out) < 20 or not any(k in code_out for k in ("def ", "class ", "import ")):
            logger.info("Coder returned incomplete code; retrying with pure Python standard library prompt.")
            retry_prompt = aarkaa_engine._build_chatml(
                "You are an expert Python engineer. Write a self-contained Python function or class using only Python standard library. Output code inside a python markdown block.",
                f"Write the self-contained Python function for: {query}"
            )
            raw = aarkaa_engine._generate(retry_prompt, max_new_tokens=1024, temperature=0.1, force_general=True)
            blocks = extract_code_blocks(raw)
            if blocks and blocks[0].get("code"):
                code_out = blocks[0]["code"]
            else:
                code_out = raw.strip()
            code_out = "\n".join(l for l in code_out.splitlines() if not l.strip().startswith(("pip ", "npm ", "$ "))).strip()
        return code_out
    except Exception as exc:
        logger.error("generate_code failed: %s", exc)
        return ""


def extract_code_blocks(text: str) -> list[dict]:
    """
    Extract all fenced code blocks from markdown text or Action Input payloads.
    Returns list of {"language": str, "code": str}.
    """
    if not text or not text.strip():
        return []

    # 1. Direct Python AST test: if text itself is already valid Python code, return it directly
    try:
        import ast
        ast.parse(text)
        return [{"language": "python", "code": text.strip()}]
    except Exception:
        pass

    # 2. Extract markdown code fences: ```python ... ``` or ``` ... ```
    pattern = r"```(?:[a-zA-Z0-9_\+\-]*)\s*\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    blocks = []
    for code in matches:
        code_clean = code.strip()
        if code_clean:
            blocks.append({"language": "python", "code": code_clean})

    if blocks:
        return blocks

    # 3. Action Input JSON extraction
    if "Action Input:" in text:
        import json
        for chunk in text.split("Action Input:")[1:]:
            chunk = chunk.strip()
            if chunk.startswith("{"):
                try:
                    end_pos = chunk.find("}\n")
                    if end_pos == -1:
                        end_pos = chunk.find("}")
                    if end_pos != -1:
                        payload = json.loads(chunk[:end_pos+1])
                        code_str = payload.get("content") or payload.get("code")
                        if code_str:
                            blocks.append({"language": "python", "code": code_str.strip()})
                except Exception:
                    pass
        if blocks:
            return blocks

    # 4. Filter out bash commands like 'pip install' and ReAct scaffolding
    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("pip ") or stripped.startswith("npm ") or stripped.startswith("$ "):
            continue
        if any(stripped.lower().startswith(p) for p in ["thought:", "action:", "observation:", "final answer:"]):
            continue
        cleaned_lines.append(line)

    candidate = "\n".join(cleaned_lines).strip()
    try:
        import ast
        ast.parse(candidate)
        return [{"language": "python", "code": candidate}]
    except Exception:
        pass

    return [{"language": "python", "code": candidate if candidate else text.strip()}]


def validate_code(code: str) -> Dict[str, Any]:
    """
    Run static analysis (AST syntax check, duplicate method check) and security scan.
    Returns {"syntax_valid": bool, "syntax_error": str|None, "security_issues": list}.
    """
    import ast
    from modules.cvr_pipeline import StaticAnalyzer, SecurityScanner
    
    target_code = code.strip()
    blocks = extract_code_blocks(target_code)
    if blocks and blocks[0].get("code"):
        target_code = blocks[0]["code"]
    
    # Auto-repair unclosed docstrings caused by token budget or repetition termination
    t_quote = chr(34) * 3
    s_quote = chr(39) * 3
    if target_code.count(t_quote) % 2 != 0:
        target_code += '\n    ' + t_quote + '\n    pass\n'
    if target_code.count(s_quote) % 2 != 0:
        target_code += '\n    ' + s_quote + '\n    pass\n'

    syntax_result = StaticAnalyzer.verify_syntax(target_code)
    security_issues = SecurityScanner.scan(code)
    
    if not syntax_result["valid"]:
        return {
            "syntax_valid": False,
            "syntax_error": syntax_result.get("error"),
            "security_issues": security_issues
        }
        
    # Check for duplicate method definitions and undefined variables using AST
    try:
        tree = ast.parse(target_code)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                seen_methods = set()
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if item.name in seen_methods:
                            return {
                                "syntax_valid": False,
                                "syntax_error": f"Code Quality Error: Duplicate method definition '{item.name}' inside class '{node.name}'.",
                                "security_issues": security_issues
                            }
                        seen_methods.add(item.name)
            # Catch raw unimported 'date.today()' usage when 'date' module was not imported
            elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                if node.value.id == "date" and "from datetime import date" not in code and "import date" not in code and "datetime.date" not in code:
                    return {
                        "syntax_valid": False,
                        "syntax_error": "Code Quality Error: Unbound variable 'date' referenced. Use 'from datetime import datetime, date' or 'datetime.now()'.",
                        "security_issues": security_issues
                    }
    except Exception:
        pass
    
    return {
        "syntax_valid": True,
        "syntax_error": None,
        "security_issues": security_issues
    }


def generate_tests(query: str, code: str) -> str:
    """
    Auto-generate pytest-style unit tests for the given code using the coder model.
    """
    from modules import aarkaa_engine
    
    aarkaa_engine.request_domain.set("technology")
    
    system_prompt = (
        "You are a test engineer. Generate comprehensive pytest-style unit tests "
        "for the provided code. Include edge cases, boundary conditions, and expected outputs. "
        "Output ONLY the test code inside a single markdown code block. "
        "Do NOT import the code — paste the functions directly above the tests so the file is self-contained. "
        "Use assert statements. Include at least 3 test functions."
    )
    
    prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
    prompt += f"<|im_start|>user\nOriginal request: {query}\n\nCode to test:\n```python\n{code}\n```<|im_end|>\n"
    prompt += "<|im_start|>assistant\n"
    
    try:
        raw = aarkaa_engine._generate(
            prompt,
            max_new_tokens=1536,
            temperature=0.2,
            force_general=False
        )
        # Extract just the test code
        blocks = extract_code_blocks(raw)
        if blocks:
            return blocks[0]["code"]
        return raw.strip()
    except Exception as exc:
        logger.error("generate_tests failed: %s", exc)
        return ""


def execute_in_sandbox(code: str, timeout: float = 10.0) -> Dict[str, Any]:
    """
    Execute Python code in the secure sandbox.
    Returns {"success": bool, "stdout": str, "stderr": str, "duration": float}.
    """
    import subprocess
    import sys
    import uuid
    from pathlib import Path
    from config import SAFE_WORK_DIR
    
    work_dir = SAFE_WORK_DIR
    work_dir.mkdir(parents=True, exist_ok=True)
    
    filename = f"coder_sandbox_{uuid.uuid4().hex[:8]}.py"
    temp_file = work_dir / filename
    
    try:
        temp_file.write_text(code, encoding="utf-8")
        start = time.perf_counter()
        
        result = subprocess.run(
            [sys.executable, filename],
            cwd=str(work_dir),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout
        )
        duration = time.perf_counter() - start
        
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "duration": round(duration, 3)
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Execution timed out after {timeout}s",
            "duration": timeout
        }
    except Exception as exc:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(exc),
            "duration": 0.0
        }
    finally:
        try:
            temp_file.unlink(missing_ok=True)
        except Exception:
            pass


def run_coder_pipeline(query: str, context: str = "") -> Dict[str, Any]:
    """
    Full Aarka Coder Pipeline:
      1. Generate code with coder-3b
      2. Extract code blocks
      3. Validate (AST + security)
      4. Generate tests
      5. Execute code + tests in sandbox
      6. Return structured result
    """
    start = time.perf_counter()
    result = {
        "code": "",
        "language": "python",
        "raw_response": "",
        "syntax_valid": False,
        "syntax_error": None,
        "security_issues": [],
        "test_code": "",
        "test_passed": False,
        "test_output": "",
        "execution_output": "",
        "execution_success": False,
        "duration": 0.0,
    }
    
    # Step 1: Generate code
    logger.info("[AarkaCoder] Step 1: Generating code for: %.80s...", query)
    raw_response = generate_code(query, context)
    result["raw_response"] = raw_response
    
    if not raw_response:
        logger.warning("[AarkaCoder] Code generation returned empty response.")
        result["duration"] = round(time.perf_counter() - start, 3)
        return result
    
    # Step 2: Extract code blocks
    logger.info("[AarkaCoder] Step 2: Extracting code blocks...")
    blocks = extract_code_blocks(raw_response)
    if not blocks:
        logger.warning("[AarkaCoder] No code blocks found in generated response.")
        result["code"] = raw_response  # Use raw as fallback
        result["duration"] = round(time.perf_counter() - start, 3)
        return result
    
    primary_block = blocks[0]
    result["code"] = primary_block["code"]
    result["language"] = primary_block["language"]
    
    # Step 3: Validate (only for Python)
    if result["language"] in ("python", "py", ""):
        logger.info("[AarkaCoder] Step 3: Validating code (AST + security)...")
        validation = validate_code(result["code"])
        result["syntax_valid"] = validation["syntax_valid"]
        result["syntax_error"] = validation.get("syntax_error")
        result["security_issues"] = validation["security_issues"]
        
        if not result["syntax_valid"]:
            logger.warning("[AarkaCoder] Syntax validation failed: %s", result["syntax_error"])
            # Still continue — let the 7B model explain the error
    else:
        # Non-Python languages: skip AST validation
        result["syntax_valid"] = True
    
    # Step 4: Execute the code itself
    if result["syntax_valid"] and result["language"] in ("python", "py", ""):
        logger.info("[AarkaCoder] Step 4: Executing code in sandbox...")
        exec_result = execute_in_sandbox(result["code"])
        result["execution_output"] = exec_result["stdout"]
        result["execution_success"] = exec_result["success"]
        if exec_result["stderr"]:
            result["execution_output"] += f"\nSTDERR: {exec_result['stderr']}"
    
    # Step 5: Generate and run tests
    if result["syntax_valid"] and result["language"] in ("python", "py", ""):
        logger.info("[AarkaCoder] Step 5: Generating unit tests...")
        test_code = generate_tests(query, result["code"])
        result["test_code"] = test_code
        
        if test_code:
            logger.info("[AarkaCoder] Step 5b: Running tests in sandbox...")
            # The test file should be self-contained (code + tests)
            test_result = execute_in_sandbox(test_code)
            result["test_passed"] = test_result["success"]
            result["test_output"] = test_result["stdout"]
            if test_result["stderr"]:
                result["test_output"] += f"\nSTDERR: {test_result['stderr']}"
    
    result["duration"] = round(time.perf_counter() - start, 3)
    logger.info(
        "[AarkaCoder] Pipeline complete in %.2fs — syntax=%s, tests=%s",
        result["duration"], result["syntax_valid"], result["test_passed"]
    )
    return result
