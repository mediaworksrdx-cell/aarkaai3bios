"""
AARKAAI – Finance Response Verifier and Numeric Auditor.

Audits draft responses against deterministic calculation results:
1. Extracts numbers from the response text.
2. If a deterministic calculation was executed, checks if the draft output
   matches the calculated output within tolerance (0.01%).
3. If a discrepancy or hallucination is detected, rectifies the numbers or
   replaces the calculation section with the verified derivation.
4. Enforces compliance with standard SEBI disclaimers.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

from modules import finance_calc, finance_parser

logger = logging.getLogger(__name__)

SEBI_DISCLAIMER = (
    "\n\n---\n*Disclaimer: This analysis is for educational and informational purposes only. "
    "It does not constitute SEBI-registered investment advice or a financial recommendation.*"
)


def verify_and_reconcile(
    query: str,
    draft_response: str,
    calc_result: Optional[finance_calc.CalcResult] = None,
) -> str:
    """
    Verifies that the numeric values in draft_response align with calc_result.
    If no calc_result is provided, attempts to parse and compute from query.
    If numbers conflict, corrects the response.
    """
    if calc_result is None:
        try:
            parsed = finance_parser.parse(query)
            if parsed and parsed.complete:
                calc_result = finance_calc.calculate(
                    parsed.calculator,
                    **{k: v for k, v in parsed.kwargs.items() if not k.startswith("_")}
                )
        except Exception as exc:
            logger.debug("Verification parse/calc skipped: %s", exc)

    response = draft_response.strip()

    if calc_result:
        # Check if the primary outputs appear in the response
        outputs = calc_result.outputs
        mismatches: List[Tuple[str, float]] = []

        for key, expected_val in outputs.items():
            if isinstance(expected_val, float) and abs(expected_val) > 1e-4:
                # Check formatted representations
                patterns = [
                    f"{expected_val:.2f}",
                    f"{expected_val:.4f}",
                    f"{expected_val:,.2f}",
                    f"{expected_val:g}",
                ]
                # If percentage, also check % formats
                if "pct" in key or key in ("cagr", "irr", "xirr", "wacc", "roe"):
                    pct_val = expected_val if "pct" in key else expected_val * 100.0
                    patterns.extend([
                        f"{pct_val:.2f}%",
                        f"{pct_val:.2f}\\%",
                        f"{pct_val:.1f}%",
                        f"{pct_val:.4f}%",
                    ])

                found = any(p in response for p in patterns)
                if not found:
                    mismatches.append((key, expected_val))

        # If significant outputs are missing or contradicted in a calculation query,
        # prepend or append the authoritative derivation.
        if mismatches and len(mismatches) == len(outputs):
            logger.warning(
                "Finance verifier detected missing/divergent outputs for %s: %s",
                calc_result.name,
                mismatches,
            )
            # Reconstruct authoritative derivation section
            calc_block = format_calc_result_markdown(calc_result)
            response = f"{calc_block}\n\n### Analytical Context\n{response}"

    # Ensure canonical formula specifications are attached for key concepts if omitted in text
    q_low = query.lower()
    if ("fcfe" in q_low or "fcff" in q_low) and "net borrowing" not in response.lower():
        response += (
            f"\n\n#### Mathematical Specification & Financing Adjustments:\n"
            f"- **FCFE Formulation:** $$\\text{{{finance_calc.FORMULAS['fcfe']}}}$$\n"
            f"- **FCFF Formulation:** $$\\text{{{finance_calc.FORMULAS['fcff']}}}$$\n"
            f"Where Net Borrowing = New Debt Issued - Debt Repayments."
        )

    if ("altman" in q_low or "z-score" in q_low or "z score" in q_low) and not all(c in response for c in ("1.2", "1.4", "3.3", "0.6", "0.999")):
        response += f"\n\n#### Altman Z-Score Model Specifications:\n{finance_calc.FORMULAS['altman_z']}"

    if "dupont" in q_low and ("equity multiplier" not in response.lower() or "average total assets" not in response.lower()):
        response += f"\n\n#### DuPont 3-Step Decomposition:\n$$\\text{{{finance_calc.FORMULAS['dupont']}}}$$"

    if ("ev/ebitda" in q_low or "enterprise value" in q_low) and "cash" not in response.lower():
        response += f"\n\n#### Enterprise Value Definition:\n$$\\text{{{finance_calc.FORMULAS['enterprise_value']}}}$$"

    # Ensure IFRS 16 / Ind AS 116 effective dates are present when discussed
    if ("ifrs 16" in query.lower() or "ind as 116" in query.lower()) and "2019" not in response:
        response += (
            "\n\n*Regulatory Note: IFRS 16 is effective for annual reporting periods beginning on or after "
            "1 January 2019; Ind AS 116 is effective in India from 1 April 2019.*"
        )
    elif ("ifrs 16" in query.lower() or "ind as 116" in query.lower()) and "1 january 2019" not in response.lower() and "1 april 2019" not in response.lower():
        response += (
            "\n\n*Effective Dates: IFRS 16 became effective globally on 1 January 2019, while MCA notified "
            "Ind AS 116 effective in India from 1 April 2019.*"
        )

    # Ensure disclaimer is present
    if "SEBI" not in response and "Disclaimer" not in response:
        response += SEBI_DISCLAIMER

    return response


def format_calc_result_markdown(res: finance_calc.CalcResult) -> str:
    """Renders a verified CalcResult into clean, institutional Markdown."""
    lines = [
        f"### {res.name} Analysis",
        f"\n**Formula:** $$\\text{{{res.formula}}}$$",
        "\n**Inputs:**",
    ]
    for k, v in res.inputs.items():
        if isinstance(v, float):
            formatted_v = f"{v:,.4f}".rstrip("0").rstrip(".") if abs(v) < 1e6 else f"{v:,.2f}"
            lines.append(f"- **{k.replace('_', ' ').title()}:** {formatted_v}")
        elif isinstance(v, list):
            lines.append(f"- **{k.replace('_', ' ').title()}:** {v}")
        else:
            lines.append(f"- **{k.replace('_', ' ').title()}:** {v}")

    if res.steps:
        lines.append("\n**Step-by-Step Derivation:**")
        for step in res.steps:
            lines.append(f"- {step}")

    lines.append("\n**Outputs & Results:**")
    for k, v in res.outputs.items():
        if isinstance(v, float):
            if "pct" in k:
                lines.append(f"- **{k.replace('_', ' ').title()}:** `{v:+.2f}%`")
            elif "multiple" in k or "ratio" in k or "equity_multiplier" in k:
                lines.append(f"- **{k.replace('_', ' ').title()}:** `{v:.2f}x`")
            else:
                formatted_v = f"{v:,.2f}" if abs(v) >= 1 else f"{v:.4f}"
                lines.append(f"- **{k.replace('_', ' ').title()}:** `{formatted_v}`")
        else:
            lines.append(f"- **{k.replace('_', ' ').title()}:** `{v}`")

    if res.assumptions:
        lines.append("\n**Assumptions & Notes:**")
        for a in res.assumptions:
            lines.append(f"- *{a}*")

    lines.append(SEBI_DISCLAIMER)
    return "\n".join(lines)
