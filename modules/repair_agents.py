import logging
import re
from typing import Dict, Any, List
from modules.cvr_pipeline import StaticAnalyzer, SecurityScanner, ToolRouter

logger = logging.getLogger(__name__)

class RepairConfidenceScorer:
    """Computes confidence probabilities and risk scores for suggested repairs."""
    
    @staticmethod
    def calculate_confidence(failure_logs: str, repair_code: str) -> Dict[str, Any]:
        # Perform AST check
        syntax = StaticAnalyzer.verify_syntax(repair_code)
        syntax_score = 1.0 if syntax["valid"] else 0.0
        
        # Performance/vulnerability warning penalties
        vulnerabilities = SecurityScanner.scan(repair_code)
        sec_penalty = len(vulnerabilities) * 0.35
        
        confidence = max(0.1, syntax_score - sec_penalty)
        return {
            "confidence": confidence,
            "risk": "high" if confidence < 0.5 else "low",
            "passed_static_analysis": syntax["valid"]
        }

class ChainedRepairController:
    """Manages coordinated, multi-step repair workflows iteratively."""
    
    @classmethod
    def attempt_chained_repair(cls, query: str, buggy_code: str, test_suite: str, max_iterations: int = 3) -> Dict[str, Any]:
        current_code = buggy_code
        repair_history = []
        
        for iteration in range(max_iterations):
            logger.info("ChainedRepair: Starting iteration %d/%d", iteration + 1, max_iterations)
            
            # Syntax validation pass
            syntax = StaticAnalyzer.verify_syntax(current_code)
            if not syntax["valid"]:
                # Syntax fixer logic
                logger.info("ChainedRepair: Repairing syntax error: %s", syntax["error"])
                current_code = cls._apply_syntax_fix(current_code, syntax["error"])
                repair_history.append(f"Iteration {iteration+1}: Repaired syntax error.")
                continue
                
            # Security scan checks
            vulnerabilities = SecurityScanner.scan(current_code)
            if vulnerabilities:
                logger.info("ChainedRepair: Repairing security vulnerabilities: %s", vulnerabilities)
                current_code = cls._apply_security_fix(current_code, vulnerabilities)
                repair_history.append(f"Iteration {iteration+1}: Repaired security vulnerabilities.")
                continue

            # Run tests to catch logical or runtime errors
            test_run = ToolRouter.run_test_script(current_code, test_suite)
            if test_run["passed"]:
                logger.info("ChainedRepair: All tests passed successfully!")
                return {
                    "success": True,
                    "repaired_code": current_code,
                    "iterations": iteration + 1,
                    "history": repair_history
                }
            else:
                logger.info("ChainedRepair: Test failed. Output: %s", test_run["stderr"])
                # Logic repair logic
                current_code = cls._apply_logic_fix(current_code, test_run["stderr"])
                repair_history.append(f"Iteration {iteration+1}: Repaired runtime error.")
                
        return {
            "success": False,
            "repaired_code": current_code,
            "iterations": max_iterations,
            "history": repair_history
        }

    @staticmethod
    def _apply_syntax_fix(code: str, error_detail: Dict[str, Any]) -> str:
        # Static mock syntax repair for prototypes
        lines = code.split("\n")
        err_line = error_detail.get("line", 1) - 1
        if 0 <= err_line < len(lines):
            line_str = lines[err_line]
            # Simple bracket balancing
            if "(" in line_str and ")" not in line_str:
                lines[err_line] = line_str + ")"
            else:
                lines[err_line] = line_str + ")"
        else:
            code += ")"
            return code
        return "\n".join(lines)


    @staticmethod
    def _apply_security_fix(code: str, vulnerabilities: List[str]) -> str:
        # If no vulnerabilities are reported, return original code
        if not vulnerabilities:
            return code
            
        try:
            import ast
            
            class SecurityRepairTransformer(ast.NodeTransformer):
                def visit_Call(self, node):
                    # Resolve function and module attributes
                    func_name = ""
                    module_name = ""
                    if isinstance(node.func, ast.Attribute):
                        func_name = node.func.attr
                        if isinstance(node.func.value, ast.Name):
                            module_name = node.func.value.id
                    elif isinstance(node.func, ast.Name):
                        func_name = node.func.id
                        
                    # 1. Handle subprocess calls containing shell=True
                    if (module_name == "subprocess" or func_name in ["subprocess", "Popen", "call", "check_call", "check_output", "run"]) and func_name in ["run", "Popen", "call", "check_call", "check_output"]:
                        new_keywords = []
                        has_shell = False
                        for kw in node.keywords:
                            if kw.arg == "shell":
                                has_shell = True
                                # Change shell to False Constant
                                new_keywords.append(ast.keyword(arg="shell", value=ast.Constant(value=False)))
                            else:
                                new_keywords.append(kw)
                        if not has_shell:
                            new_keywords.append(ast.keyword(arg="shell", value=ast.Constant(value=False)))
                        
                        node.keywords = new_keywords
                        
                        # Fix command argument to be a list if it's a single constant string
                        if node.args:
                            first_arg = node.args[0]
                            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                                parts = first_arg.value.split()
                                node.args[0] = ast.List(elts=[ast.Constant(value=p) for p in parts], ctx=ast.Load())
                        return node
                        
                    # 2. Handle os.system or general system/popen calls
                    if (module_name == "os" and func_name in ["system", "popen"]) or (func_name in ["system", "popen"] and not module_name):
                        # Create a safe subprocess.run call
                        sub_run_func = ast.Attribute(
                            value=ast.Name(id="subprocess", ctx=ast.Load()),
                            attr="run",
                            ctx=ast.Load()
                        )
                        
                        # Generate the arguments list for the subprocess run call
                        run_args = []
                        if node.args:
                            first_arg = node.args[0]
                            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                                parts = first_arg.value.split()
                                run_args.append(ast.List(elts=[ast.Constant(value=p) for p in parts], ctx=ast.Load()))
                            else:
                                # Fallback to using split() if the argument is a variable expression
                                split_call = ast.Call(
                                    func=ast.Attribute(value=first_arg, attr="split", ctx=ast.Load()),
                                    args=[],
                                    keywords=[]
                                )
                                run_args.append(split_call)
                        else:
                            run_args.append(ast.List(elts=[], ctx=ast.Load()))
                            
                        # Add shell=False kwarg
                        run_keywords = [
                            ast.keyword(arg="shell", value=ast.Constant(value=False))
                        ]
                        
                        # Build the safe node
                        new_call = ast.Call(
                            func=sub_run_func,
                            args=run_args,
                            keywords=run_keywords
                        )
                        return ast.copy_location(new_call, node)
                        
                    return node

            tree = ast.parse(code)
            transformer = SecurityRepairTransformer()
            modified_tree = transformer.visit(tree)
            ast.fix_missing_locations(modified_tree)
            import astunparse
            repaired_code = astunparse.unparse(modified_tree).strip()
            
            # Prepend import subprocess if required
            if "import subprocess" not in repaired_code:
                repaired_code = "import subprocess\n" + repaired_code
            return repaired_code
            
        except Exception as e:
            # Fallback to safe regex repairs if astunparse or AST rewriting encounters edge errors
            for vuln in vulnerabilities:
                if "shell=True" in vuln:
                    code = re.sub(
                        r"subprocess\.(run|Popen|call)\(\s*['\"](.*?)['\"]\s*,\s*shell\s*=\s*True\s*\)",
                        r"subprocess.\1(['\2'], shell=False)",
                        code
                    )
                if "os.system" in vuln or "system" in vuln or "popen" in vuln:
                    def repl(match):
                        cmd_arg = match.group(1).strip()
                        if (cmd_arg.startswith("'") and cmd_arg.endswith("'")) or (cmd_arg.startswith('"') and cmd_arg.endswith('"')):
                            inner = cmd_arg[1:-1]
                            parts = inner.split()
                            list_str = ", ".join([f'"{p}"' for p in parts])
                            return f"subprocess.run([{list_str}], shell=False)"
                        return f"subprocess.run({cmd_arg}.split(), shell=False)"
                    code = re.sub(
                        r"(?:os\.)?(?:system|popen)\((.*?)\)",
                        repl,
                        code
                    )
            if "import subprocess" not in code:
                code = "import subprocess\n" + code
            return code

    @staticmethod
    def _apply_logic_fix(code: str, test_stderr: str) -> str:
        # Simple string-reverse logical correction heuristic
        if "AssertionError" in test_stderr or "reversed" in test_stderr:
            # Fix iterator logic: reverse strings properly
            code = code.replace("reversed(s)", "s[::-1]")
            code = code.replace("reversed(x)", "x[::-1]")
        return code
