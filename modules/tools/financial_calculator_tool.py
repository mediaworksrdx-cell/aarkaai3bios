"""
AARKAAI – FinancialCalculatorTool.

Thin adapter over ``modules.finance_calc``. Every argument is required unless
the underlying formula marks it optional; missing inputs return an explicit
error instead of being silently replaced by defaults.
"""
import inspect
import json
import logging
from typing import Any, Dict

from modules import finance_calc
from modules.tools.base import Tool

logger = logging.getLogger(__name__)


def _signature_help(name: str) -> str:
    sig = inspect.signature(finance_calc.CALCULATORS[name])
    return f"{name}({', '.join(sig.parameters)})"


class FinancialCalculatorTool(Tool):
    name = "FinancialCalculatorTool"
    description = (
        "Deterministic finance calculator. Pass action=<calculator> plus its arguments "
        "(rates as decimals, e.g. 0.12). Actions: " + ", ".join(sorted(finance_calc.CALCULATORS))
    )
    risk_level = "SAFE"
    latency_weight = 0.3
    cost_weight = 0.1
    base_confidence = 0.99
    permissions = ["read"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 50

    def execute(self, params: Dict[str, Any]) -> str:
        action = params.get("action")
        if action not in finance_calc.CALCULATORS:
            return f"Error: unknown action {action!r}. Available: {sorted(finance_calc.CALCULATORS)}"
        fn = finance_calc.CALCULATORS[action]
        kwargs = {k: v for k, v in params.items() if k != "action"}
        sig = inspect.signature(fn)
        accepts_var_kw = any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values())
        missing = [p.name for p in sig.parameters.values()
                   if p.default is p.empty and p.kind not in (p.VAR_KEYWORD, p.VAR_POSITIONAL)
                   and p.name not in kwargs]
        if missing:
            return f"Error: missing required arguments {missing}. Usage: {_signature_help(action)}"
        if not accepts_var_kw:
            unknown = [k for k in kwargs if k not in sig.parameters]
            if unknown:
                return f"Error: unknown arguments {unknown}. Usage: {_signature_help(action)}"
        try:
            res = fn(**kwargs)
        except finance_calc.FinanceDomainError as e:
            return f"Error: invalid input — {e}"
        except Exception as e:
            logger.error("FinancialCalculatorTool %s failed: %s", action, e)
            return f"Error: {e}"
        return json.dumps({"calculator": res.name, "formula": res.formula, "inputs": res.inputs,
                           "outputs": res.outputs, "steps": res.steps, "assumptions": res.assumptions},
                          default=str)
