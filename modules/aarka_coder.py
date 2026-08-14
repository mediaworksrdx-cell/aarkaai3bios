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
    Generate raw code using the coder-3b model.
    Uses request_domain='technology' to route to coder model.
    """
    from modules import aarkaa_engine
    
    # Force coder model routing
    aarkaa_engine.request_domain.set("technology")
    
    system_prompt = (
        "You are Aarka Coder, a Principal Software Architect and Quantitative Systems Engineer. "
        "Generate production-grade, complete, mathematically exact code adhering strictly to specifications. "
        "FORBIDDEN: Undefined variables (`price`, `current_price`), missing arguments in method calls, missing imports (`from datetime import datetime, date`), duplicate method definitions, or unhandled overselling.\n"
        "PRODUCTION PORTFOLIO ACCOUNTING REQUIREMENTS:\n"
        "1. IMPORTS & INSTANCE STATE:\n"
        "   - Top of file: `from collections import defaultdict, deque` and `from datetime import datetime, date`.\n"
        "   - Class attributes: `self.portfolio = defaultdict(deque)` (stores open buy lots `[qty, buy_price, buy_date]`) and `self.realized_pnl = 0.0` (accumulates P&L across all sales).\n"
        "2. OVERSELLING CHECK:\n"
        "   - In `sell_stock(self, symbol: str, quantity: int, sell_price: float, sell_date: datetime) -> float`:\n"
        "     `total_available = sum(lot[0] for lot in self.portfolio[symbol])`\n"
        "     `if quantity > total_available: raise ValueError(f'Insufficient shares to sell {quantity} of {symbol}. Available: {total_available}')`\n"
        "3. FIFO SALE PROCESSING:\n"
        "     `trade_pnl = 0.0`\n"
        "     `while quantity > 0 and self.portfolio[symbol]:`\n"
        "       `lot = self.portfolio[symbol].popleft()`\n"
        "       `matched = min(quantity, lot[0])`\n"
        "       `trade_pnl += matched * (sell_price - lot[1])`\n"
        "       `quantity -= matched`\n"
        "       `lot[0] -= matched`\n"
        "       `if lot[0] > 0: self.portfolio[symbol].appendleft(lot)`\n"
        "     `self.realized_pnl += trade_pnl`\n"
        "     `return trade_pnl`\n"
        "4. VALUATION & UNREALIZED P&L:\n"
        "   - `get_realized_pnl(self) -> float`: Returns `self.realized_pnl`.\n"
        "   - `get_unrealized_pnl(self, current_prices: dict[str, float]) -> float`:\n"
        "     Returns sum over all open lots of `lot[0] * (current_prices.get(symbol, lot[1]) - lot[1])`.\n"
        "   - `get_portfolio_value(self, current_prices: dict[str, float]) -> float`:\n"
        "     Returns sum over all open lots of `lot[0] * current_prices.get(symbol, lot[1])`.\n"
        "5. CAGR:\n"
        "   - `get_cagr(self, symbol: str, current_price: float, current_date: datetime) -> float`:\n"
        "     `total_shares = sum(lot[0] for lot in self.portfolio[symbol])`\n"
        "     `total_cost = sum(lot[0] * lot[1] for lot in self.portfolio[symbol])`\n"
        "     `current_val = total_shares * current_price`\n"
        "     `weighted_days = sum(lot[0] * (current_date - lot[2]).days for lot in self.portfolio[symbol]) / total_shares`\n"
        "     `years = weighted_days / 365.25`\n"
        "     `return ((current_val / total_cost) ** (1.0 / years)) - 1.0` if years > 0 and total_cost > 0 else 0.0\n"
        "6. TEST SUITE & COMPLEXITY:\n"
        "   - Provide complete pytest test cases verifying multi-symbol, multi-lot FIFO, partial sells, overselling exception, realized/unrealized P&L, portfolio market value, and CAGR.\n"
        "   - Include explicit Complexity Analysis section.\n"
        "Output ONLY fully functional, executable Python code inside a single markdown block."
    )
    
    prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n"
    if context:
        prompt += f"<|im_start|>user\nContext: {context[:2000]}\n\n{query}<|im_end|>\n"
    else:
        prompt += f"<|im_start|>user\n{query}<|im_end|>\n"
    prompt += "<|im_start|>assistant\n"
    
    try:
        raw = aarkaa_engine._generate(
            prompt, 
            max_new_tokens=2048, 
            temperature=0.2,
            force_general=False  # Use coder model
        )
        # Sanitize any accidental ReAct scaffolding tags
        clean_lines = []
        for line in raw.split("\n"):
            line_strip = line.strip().lower()
            if (line_strip.startswith("thought:") or 
                line_strip.startswith("action:") or 
                line_strip.startswith("action input:") or 
                line_strip.startswith("observation:")):
                continue
            clean_lines.append(line)
        return "\n".join(clean_lines).strip()
    except Exception as exc:
        logger.error("generate_code failed: %s", exc)
        return ""


def extract_code_blocks(text: str) -> list[dict]:
    """
    Extract all fenced code blocks from markdown text.
    Returns list of {"language": str, "code": str}.
    """
    pattern = r"```(\w*)\n(.*?)```"
    matches = re.findall(pattern, text, re.DOTALL)
    blocks = []
    for lang, code in matches:
        lang = lang.strip().lower() or "python"
        blocks.append({"language": lang, "code": code.strip()})
    
    # If no fenced blocks found, try to extract code-like content
    if not blocks:
        lines = text.strip().split("\n")
        code_lines = []
        for line in lines:
            stripped = line.strip()
            # Heuristic: lines that look like code
            if (stripped.startswith("def ") or stripped.startswith("class ") or
                stripped.startswith("import ") or stripped.startswith("from ") or
                stripped.startswith("    ") or stripped.startswith("\t") or
                stripped.startswith("#") or stripped.startswith("return ") or
                "=" in stripped or stripped.startswith("if ") or
                stripped.startswith("for ") or stripped.startswith("while ") or
                stripped.startswith("print(")):
                code_lines.append(line)
        if code_lines:
            blocks.append({"language": "python", "code": "\n".join(code_lines).strip()})
    
    return blocks


def validate_code(code: str) -> Dict[str, Any]:
    """
    Run static analysis (AST syntax check, duplicate method check) and security scan.
    Returns {"syntax_valid": bool, "syntax_error": str|None, "security_issues": list}.
    """
    import ast
    from modules.cvr_pipeline import StaticAnalyzer, SecurityScanner
    
    syntax_result = StaticAnalyzer.verify_syntax(code)
    security_issues = SecurityScanner.scan(code)
    
    if not syntax_result["valid"]:
        return {
            "syntax_valid": False,
            "syntax_error": syntax_result.get("error"),
            "security_issues": security_issues
        }
        
    # Check for duplicate method definitions and undefined variables using AST
    try:
        tree = ast.parse(code)
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
