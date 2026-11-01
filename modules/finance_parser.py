"""
AARKAAI – Finance query parser.

Converts natural-language finance questions into a calculator name plus
validated keyword arguments for ``modules.finance_calc``. The parser only
*extracts* numbers the user wrote; it never supplies economic assumptions.
If a required input is missing it is reported back so the agent can ask the
user (or let a model extract it from context) instead of guessing.

Unit multipliers below are definitions of the Indian/International numbering
systems, not data values.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

# ─────────────────────────────── quantities ───────────────────────────────────

_SCALE = {
    "crore": 1e7, "crores": 1e7, "cr": 1e7,
    "lakh": 1e5, "lakhs": 1e5, "lac": 1e5, "lacs": 1e5, "l": 1e5,
    "thousand": 1e3, "k": 1e3,
    "million": 1e6, "mn": 1e6, "m": 1e6,
    "billion": 1e9, "bn": 1e9, "b": 1e9,
    "trillion": 1e12, "tn": 1e12,
}
_DURATION = {
    "year": "years", "years": "years", "yr": "years", "yrs": "years", "y": "years",
    "month": "months", "months": "months", "mo": "months", "mos": "months",
    "day": "days", "days": "days", "d": "days",
}

_NUM = r"[-−]?\(?\d[\d,]*(?:\.\d+)?\)?|[-−]?\.\d+"
_QTY_RE = re.compile(
    r"(?P<cur>₹|rs\.?|inr|\$|usd|€|£)?\s*"
    r"(?P<num>" + _NUM + r")"
    r"\s*(?P<pct>%|percent\b|pct\b)?"
    r"(?:\s*(?P<scale>crores?|cr|lakhs?|lacs?|l|thousand|k|million|mn|m|billion|bn|b|trillion|tn)\b)?"
    r"(?:\s*(?P<dur>years?|yrs?|y|months?|mos?|mo|days?|d)\b)?",
    re.IGNORECASE,
)


@dataclass
class Quantity:
    value: float
    kind: str           # money | pct | years | months | days | plain
    start: int
    end: int
    raw: str


def _to_float(s: str) -> float:
    s = s.replace("−", "-").replace(",", "")
    neg = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    v = float(s)
    return -v if neg else v


def extract_quantities(text: str) -> List[Quantity]:
    out: List[Quantity] = []
    for m in _QTY_RE.finditer(text):
        num = m.group("num")
        if not num or not re.search(r"\d", num):
            continue
        # Skip digits that are part of identifiers (e.g. "Q3", "IFRS16", "T+1")
        if m.start("num") > 0 and text[m.start("num") - 1].isalpha() and not m.group("cur"):
            continue
        val = _to_float(num)
        kind = "plain"
        if m.group("pct"):
            kind, val = "pct", val / 100.0
        scale = (m.group("scale") or "").lower()
        if scale:
            # Single-letter scales (k, m, b, l) are accepted only when attached
            # directly to the number or preceded by a currency symbol.
            attached = m.start("scale") == m.end("num") + (len(m.group("pct") or ""))
            if len(scale) == 1 and not (m.group("cur") or attached):
                scale = ""
            if scale:
                val *= _SCALE[scale]
                kind = "money"
        dur = (m.group("dur") or "").lower()
        if dur and kind != "pct":
            kind = _DURATION[dur]
        if m.group("cur") and kind == "plain":
            kind = "money"
        out.append(Quantity(val, kind, m.start(), m.end(), m.group(0).strip()))
    return out


def _labeled(text: str, aliases: Sequence[str], kinds: Optional[Sequence[str]] = None) -> Optional[Quantity]:
    """Find the quantity nearest *after* (preferred) or before an alias phrase."""
    low = text.lower()
    qs = extract_quantities(text)
    best: Optional[Tuple[int, Quantity]] = None
    for alias in aliases:
        for am in re.finditer(r"(?<![a-z])" + re.escape(alias) + r"(?![a-z])", low):
            for q in qs:
                if kinds and q.kind not in kinds:
                    continue
                if q.start >= am.end():
                    gap = low[am.end():q.start]
                    if len(gap) <= 25 and not re.search(r"[;\n]", gap):
                        d = len(gap)
                    else:
                        continue
                elif q.end <= am.start():
                    gap = low[q.end:am.start()]
                    if len(gap) <= 6:
                        d = len(gap) + 30   # before-alias matches rank lower
                    else:
                        continue
                else:
                    continue
                if best is None or d < best[0]:
                    best = (d, q)
    return best[1] if best else None


def _number_list(text: str, aliases: Sequence[str]) -> Optional[List[float]]:
    low = text.lower()
    for alias in aliases:
        m = re.search(re.escape(alias) + r"\s*(?:of|are|is|=|:)?\s*\[?\s*((?:" + _NUM +
                      r")(?:\s*[a-z₹$]{0,6}\s*(?:,|;|and|then|\s)\s*(?:" + _NUM + r"))+)", low)
        if m:
            nums = re.findall(_NUM, m.group(1))
            vals = [_to_float(n) for n in nums]
            if len(vals) >= 2:
                return vals
    return None


def _years(text: str) -> Optional[float]:
    for q in extract_quantities(text):
        if q.kind == "years":
            return q.value
        if q.kind == "months":
            return q.value / 12.0
    return None


def _months(text: str) -> Optional[float]:
    for q in extract_quantities(text):
        if q.kind == "months":
            return q.value
        if q.kind == "years":
            return q.value * 12.0
    return None


def _first(qs: List[Quantity], kinds: Sequence[str]) -> Optional[Quantity]:
    return next((q for q in qs if q.kind in kinds), None)


def _val(q: Optional[Quantity]) -> Optional[float]:
    return None if q is None else q.value


# Compounding vocabulary → periods per year (definitions)
_FREQ = {"daily": 365, "monthly": 12, "quarterly": 4, "half-yearly": 2, "half yearly": 2,
         "semi-annual": 2, "semi-annually": 2, "semiannual": 2, "annually": 1, "annual": 1, "yearly": 1}


def _frequency(text: str) -> Optional[int]:
    low = text.lower()
    for word, n in sorted(_FREQ.items(), key=lambda kv: -len(kv[0])):
        if re.search(r"(?<![a-z])" + re.escape(word) + r"(?![a-z])", low):
            return n
    return None


# ─────────────────────────────── parse result ─────────────────────────────────

@dataclass
class ParsedCalc:
    calculator: str
    kwargs: Dict[str, Any]
    missing: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def complete(self) -> bool:
        return not self.missing


def _finish(name: str, kwargs: Dict[str, Any], required: Sequence[str],
            notes: Optional[List[str]] = None) -> ParsedCalc:
    clean = {k: v for k, v in kwargs.items() if v is not None}
    return ParsedCalc(name, clean, [r for r in required if clean.get(r) is None], notes or [])


# ─────────────────────────────── extractors ───────────────────────────────────

def _p_cagr(t: str) -> ParsedCalc:
    m = re.search(r"from\s+(.+?)\s+to\s+(.+?)\s+(?:over|in|across|within)\s+(.+?(?:years?|yrs?|months?))", t, re.I)
    v0 = v1 = n = None
    if m:
        a, b = extract_quantities(m.group(1)), extract_quantities(m.group(2))
        v0 = a[0].value if a else None
        v1 = b[0].value if b else None
        n = _years(m.group(3))
    v0 = v0 if v0 is not None else _val(_labeled(t, ["initial value", "beginning value", "start value", "initial", "invested"], ["money", "plain"]))
    v1 = v1 if v1 is not None else _val(_labeled(t, ["final value", "ending value", "end value", "final", "grew to", "now worth"], ["money", "plain"]))
    n = n if n is not None else _years(t)
    return _finish("cagr", {"initial_value": v0, "final_value": v1, "years": n},
                   ["initial_value", "final_value", "years"])


def _p_emi(t: str) -> ParsedCalc:
    qs = extract_quantities(t)
    p = _labeled(t, ["loan of", "loan amount", "principal", "borrow", "loan"], ["money", "plain"])
    if p is None:
        monies = [q for q in qs if q.kind == "money"]
        p = max(monies, key=lambda q: q.value) if monies else None
    r = _labeled(t, ["interest rate", "rate of", "rate", "at", "interest"], ["pct"]) or _first(qs, ["pct"])
    return _finish("emi", {"principal": _val(p), "annual_rate": _val(r), "months": _months(t)},
                   ["principal", "annual_rate", "months"])


def _p_sip(t: str) -> ParsedCalc:
    qs = extract_quantities(t)
    p = _labeled(t, ["sip of", "monthly sip", "per month", "monthly investment", "invest", "sip"], ["money", "plain"])
    r = _labeled(t, ["return of", "expected return", "returns", "return", "rate", "at"], ["pct"]) or _first(qs, ["pct"])
    timing = "end" if re.search(r"end of (?:each|the|every) month", t, re.I) else "begin"
    notes = [] if timing == "end" or re.search(r"beginning|start of", t, re.I) else \
        ["Contribution timing not stated; using start-of-month (annuity-due) convention"]
    return _finish("sip", {"monthly_investment": _val(p), "annual_rate": _val(r), "years": _years(t),
                           "timing": timing}, ["monthly_investment", "annual_rate", "years"], notes)


def _p_compound(t: str) -> ParsedCalc:
    qs = extract_quantities(t)
    p = _labeled(t, ["principal", "invest", "deposit", "amount", "lumpsum", "lump sum", "on"], ["money", "plain"]) \
        or _first(qs, ["money"]) or max((q for q in qs if q.kind == "plain"), key=lambda q: q.value, default=None)
    r = _labeled(t, ["interest rate", "rate", "at", "return"], ["pct"]) or _first(qs, ["pct"])
    freq = _frequency(t)
    kwargs = {"principal": _val(p), "annual_rate": _val(r), "years": _years(t)}
    if freq is None:
        return _finish("lumpsum", kwargs, ["principal", "annual_rate", "years"],
                       ["Compounding frequency not stated; compounding annually"])
    kwargs["periods_per_year"] = freq
    return _finish("compound_interest", kwargs, ["principal", "annual_rate", "years", "periods_per_year"])


def _p_npv(t: str) -> ParsedCalc:
    r = _labeled(t, ["discount rate", "rate of", "rate", "wacc", "at"], ["pct"])
    cfs = _number_list(t, ["cash flows", "cashflows", "cash flow", "flows"])
    return _finish("npv", {"rate": _val(r), "cash_flows": cfs}, ["rate", "cash_flows"],
                   ["First cash flow treated as t=0 (undiscounted)"])


def _p_irr(t: str) -> ParsedCalc:
    cfs = _number_list(t, ["cash flows", "cashflows", "cash flow", "flows"])
    return _finish("irr", {"cash_flows": cfs}, ["cash_flows"])


def _p_payback(t: str) -> ParsedCalc:
    return _finish("payback", {"cash_flows": _number_list(t, ["cash flows", "cashflows", "flows"])}, ["cash_flows"])


def _p_capm(t: str) -> ParsedCalc:
    rf = _labeled(t, ["risk-free rate", "risk free rate", "risk-free", "risk free", "rf"], ["pct"])
    b = _labeled(t, ["beta", "β"], ["plain"])
    rm = _labeled(t, ["market return", "expected market return", "rm"], ["pct"])
    erp = _labeled(t, ["equity risk premium", "market risk premium", "erp", "mrp"], ["pct"])
    rmv = _val(rm)
    if rmv is None and erp is not None and rf is not None:
        rmv = rf.value + erp.value
    return _finish("capm", {"risk_free_rate": _val(rf), "beta": _val(b), "market_return": rmv},
                   ["risk_free_rate", "beta", "market_return"])


def _p_wacc(t: str) -> ParsedCalc:
    e = _labeled(t, ["equity value", "market value of equity", "equity of", "equity"], ["money", "plain"])
    d = _labeled(t, ["debt value", "market value of debt", "debt of", "debt"], ["money", "plain"])
    ke = _labeled(t, ["cost of equity", "ke", "k_e"], ["pct"])
    kd = _labeled(t, ["cost of debt", "pre-tax cost of debt", "kd", "k_d"], ["pct"])
    tx = _labeled(t, ["tax rate", "tax"], ["pct"])
    we = _labeled(t, ["weight of equity", "equity weight"], ["pct"])
    wd = _labeled(t, ["weight of debt", "debt weight"], ["pct"])
    ev, dv = _val(e), _val(d)
    if (ev is None or dv is None) and we is not None and wd is not None:
        ev, dv = we.value, wd.value
    return _finish("wacc", {"equity_value": ev, "debt_value": dv, "cost_of_equity": _val(ke),
                            "cost_of_debt": _val(kd), "tax_rate": _val(tx)},
                   ["equity_value", "debt_value", "cost_of_equity", "cost_of_debt", "tax_rate"])


def _p_ddm(t: str) -> ParsedCalc:
    d = _labeled(t, ["current dividend", "dividend of", "dividend", "d0"], ["money", "plain"])
    g = _labeled(t, ["growth rate", "growth", "grow at", "g ="], ["pct"])
    r = _labeled(t, ["required return", "cost of equity", "discount rate", "required rate"], ["pct"])
    return _finish("ddm", {"current_dividend": _val(d), "growth_rate": _val(g), "required_return": _val(r)},
                   ["current_dividend", "growth_rate", "required_return"])


def _p_ev(t: str) -> ParsedCalc:
    mc = _labeled(t, ["market cap", "market capitalization", "market capitalisation", "mcap"], ["money", "plain"])
    d = _labeled(t, ["total debt", "debt"], ["money", "plain"])
    c = _labeled(t, ["cash and equivalents", "cash & equivalents", "cash"], ["money", "plain"])
    pf = _labeled(t, ["preferred equity", "preference capital", "preferred"], ["money", "plain"])
    mi = _labeled(t, ["minority interest", "non-controlling interest", "nci"], ["money", "plain"])
    eb = _labeled(t, ["ebitda"], ["money", "plain"])
    kw = {"market_cap": _val(mc), "total_debt": _val(d), "cash": _val(c),
          "preferred_equity": _val(pf), "minority_interest": _val(mi)}
    res = _finish("enterprise_value", kw, ["market_cap", "total_debt", "cash"])
    if eb is not None:
        res.notes.append(f"EBITDA supplied: {eb.value}")
        res.kwargs["_ebitda"] = eb.value
    return res


def _p_pe(t: str) -> ParsedCalc:
    p = _labeled(t, ["share price", "price of", "price", "trading at", "cmp"], ["money", "plain"])
    e = _labeled(t, ["eps", "earnings per share"], ["money", "plain"])
    return _finish("pe_ratio", {"price": _val(p), "eps": _val(e)}, ["price", "eps"])


def _p_dupont(t: str) -> ParsedCalc:
    ni = _labeled(t, ["net income", "net profit", "pat", "profit after tax"], ["money", "plain"])
    rev = _labeled(t, ["revenue", "sales", "turnover of"], ["money", "plain"])
    ta = _labeled(t, ["average total assets", "avg total assets", "total assets", "assets"], ["money", "plain"])
    eq = _labeled(t, ["average equity", "average shareholders' equity", "shareholders equity",
                      "shareholders' equity", "equity", "net worth"], ["money", "plain"])
    return _finish("dupont", {"net_income": _val(ni), "revenue": _val(rev), "average_total_assets": _val(ta),
                              "average_equity": _val(eq)},
                   ["net_income", "revenue", "average_total_assets", "average_equity"])


def _p_debt_ebitda(t: str) -> ParsedCalc:
    d = _labeled(t, ["total debt", "debt"], ["money", "plain"])
    e = _labeled(t, ["ebitda"], ["money", "plain"])
    c = _labeled(t, ["cash"], ["money", "plain"])
    return _finish("debt_to_ebitda", {"total_debt": _val(d), "ebitda": _val(e), "cash": _val(c)},
                   ["total_debt", "ebitda"])


def _p_icr(t: str) -> ParsedCalc:
    e = _labeled(t, ["ebit"], ["money", "plain"])
    i = _labeled(t, ["interest expense", "interest cost", "interest"], ["money", "plain"])
    return _finish("interest_coverage", {"ebit": _val(e), "interest_expense": _val(i)}, ["ebit", "interest_expense"])


def _p_real(t: str) -> ParsedCalc:
    n = _labeled(t, ["nominal return", "nominal rate", "nominal", "return of", "earning"], ["pct"])
    i = _labeled(t, ["inflation rate", "inflation", "cpi"], ["pct"])
    return _finish("real_return", {"nominal_rate": _val(n), "inflation_rate": _val(i)},
                   ["nominal_rate", "inflation_rate"])


def _p_position(t: str) -> ParsedCalc:
    c = _labeled(t, ["capital of", "capital", "account size", "account of", "portfolio of"], ["money", "plain"])
    r = _labeled(t, ["risk per trade", "risking", "risk of", "risk"], ["pct"])
    e = _labeled(t, ["entry price", "entry at", "entry", "buy at", "buying at"], ["money", "plain"])
    s = _labeled(t, ["stop loss", "stop-loss", "stoploss", "stop at", "sl", "stop"], ["money", "plain"])
    return _finish("position_size", {"capital": _val(c), "risk_fraction": _val(r), "entry_price": _val(e),
                                     "stop_loss": _val(s)}, ["capital", "risk_fraction", "entry_price", "stop_loss"])


def _p_rr(t: str) -> ParsedCalc:
    e = _labeled(t, ["entry price", "entry at", "entry", "buy at", "buying at"], ["money", "plain"])
    tg = _labeled(t, ["target price", "target at", "target", "tp"], ["money", "plain"])
    s = _labeled(t, ["stop loss", "stop-loss", "stoploss", "stop at", "sl", "stop"], ["money", "plain"])
    return _finish("risk_reward", {"entry_price": _val(e), "target_price": _val(tg), "stop_loss": _val(s)},
                   ["entry_price", "target_price", "stop_loss"])


def _p_bs(t: str) -> ParsedCalc:
    s = _labeled(t, ["spot price", "spot", "underlying price", "underlying at", "stock price", "s ="], ["money", "plain"])
    k = _labeled(t, ["strike price", "strike", "k ="], ["money", "plain"])
    v = _labeled(t, ["implied volatility", "volatility", "vol", "iv", "sigma", "σ"], ["pct"])
    r = _labeled(t, ["risk-free rate", "risk free rate", "risk-free", "interest rate", "rate"], ["pct"])
    q = _labeled(t, ["dividend yield"], ["pct"])
    tq = _labeled(t, ["expiry in", "expiring in", "time to expiry", "maturity", "expires in", "tenor"],
                  ["days", "months", "years"])
    notes: List[str] = []
    ty = None
    if tq is not None:
        ty = {"days": tq.value / 365.0, "months": tq.value / 12.0, "years": tq.value}[tq.kind]
        if tq.kind == "days":
            notes.append("Time converted with calendar days / 365")
    else:
        yy = _years(t)
        ty = yy
    ot = "put" if re.search(r"\bput\b|\bpe\b", t, re.I) else ("call" if re.search(r"\bcall\b|\bce\b", t, re.I) else None)
    kw = {"spot": _val(s), "strike": _val(k), "time_years": ty, "risk_free_rate": _val(r),
          "volatility": _val(v), "option_type": ot}
    if q is not None:
        kw["dividend_yield"] = q.value
    return _finish("black_scholes", kw, ["spot", "strike", "time_years", "risk_free_rate", "volatility", "option_type"], notes)


_LEG_RE = re.compile(
    r"(?P<side>buy|sell|long|short)(?:ing|s)?\s+(?:(?P<qty>\d+)\s*(?:x|lots?|contracts?)?\s+)?(?:an?\s+|the\s+|one\s+)?"
    r"(?:(?P<k1>\d+(?:\.\d+)?)\s*(?:strike\s+)?(?P<t1>call|put|ce|pe)s?"
    r"|(?P<t2>call|put|ce|pe)s?\s*(?:at\s+|with\s+)?(?:strike\s+|k\s*=?\s*)?(?P<k2>\d+(?:\.\d+)?))"
    r"[^.;,]*?(?:@|at|for|premium(?:\s+of)?|paying|receiving|costing)\s*(?:₹|rs\.?|\$)?\s*(?P<prem>\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


def _p_strategy(t: str) -> ParsedCalc:
    legs = []
    for m in _LEG_RE.finditer(t):
        typ = (m.group("t1") or m.group("t2")).lower()
        typ = {"ce": "call", "pe": "put"}.get(typ, typ)
        q = float(m.group("qty") or 1)
        if m.group("side").lower() in ("sell", "short"):
            q = -q
        legs.append({"type": typ, "strike": float(m.group("k1") or m.group("k2")),
                     "premium": float(m.group("prem")), "quantity": q})
    return _finish("option_strategy", {"legs": legs or None}, ["legs"])


def _p_bond(t: str) -> ParsedCalc:
    fv = _labeled(t, ["face value", "par value", "face", "par"], ["money", "plain"])
    c = _labeled(t, ["coupon rate", "coupon of", "coupon"], ["pct"])
    y = _labeled(t, ["yield to maturity", "ytm", "yield", "market rate", "discount rate"], ["pct"])
    p = _labeled(t, ["priced at", "price of", "trading at", "price"], ["money", "plain"])
    freq = _frequency(t)
    n = _years(t)
    wants_ytm = bool(re.search(r"\b(ytm|yield to maturity)\b", t, re.I)) and y is None
    if wants_ytm:
        return _finish("bond_ytm", {"price": _val(p), "face_value": _val(fv), "coupon_rate": _val(c),
                                    "years": n, "frequency": freq},
                       ["price", "face_value", "coupon_rate", "years", "frequency"])
    return _finish("bond_price", {"face_value": _val(fv), "coupon_rate": _val(c), "yield_rate": _val(y),
                                  "years": n, "frequency": freq},
                   ["face_value", "coupon_rate", "yield_rate", "years", "frequency"])


def _p_fcff(t: str) -> ParsedCalc:
    g = lambda al: _val(_labeled(t, al, ["money", "plain"]))
    return _finish("fcff", {"ebit": g(["ebit"]), "tax_rate": _val(_labeled(t, ["tax rate", "tax"], ["pct"])),
                            "depreciation_amortization": g(["depreciation and amortization", "d&a", "depreciation"]),
                            "capex": g(["capital expenditure", "capex"]),
                            "change_in_nwc": g(["change in working capital", "change in nwc", "δnwc", "increase in working capital", "working capital"])},
                   ["ebit", "tax_rate", "depreciation_amortization", "capex", "change_in_nwc"])


def _p_fcfe(t: str) -> ParsedCalc:
    g = lambda al: _val(_labeled(t, al, ["money", "plain"]))
    return _finish("fcfe", {"fcff_value": g(["fcff", "free cash flow to firm"]),
                            "interest_expense": g(["interest expense", "interest"]),
                            "tax_rate": _val(_labeled(t, ["tax rate", "tax"], ["pct"])),
                            "net_borrowing": g(["net borrowing", "net debt issued", "borrowing"])},
                   ["fcff_value", "interest_expense", "tax_rate", "net_borrowing"])


# Ordered: more specific triggers first.
_TRIGGERS: List[Tuple[str, str, Callable[[str], ParsedCalc]]] = [
    ("option_strategy", r"\b(bull call|bear put|iron condor|straddle|strangle|spread|butterfly|payoff)\b", _p_strategy),
    ("black_scholes", r"\b(black[- ]?scholes|option (?:price|premium|greeks)|greeks|delta|gamma|vega|theta)\b", _p_bs),
    ("bond", r"\b(bond|coupon|ytm|yield to maturity|duration|convexity)\b", _p_bond),
    ("cagr", r"\b(cagr|compound(?:ed)? annual growth)\b", _p_cagr),
    ("emi", r"\b(emi|loan|mortgage|instal?lment)\b", _p_emi),
    ("sip", r"\b(sip|systematic investment)\b", _p_sip),
    ("irr", r"\b(irr|internal rate of return)\b", _p_irr),
    ("npv", r"\b(npv|net present value)\b", _p_npv),
    ("payback", r"\bpayback\b", _p_payback),
    ("wacc", r"\b(wacc|weighted average cost of capital)\b", _p_wacc),
    ("capm", r"\b(capm|cost of equity)\b", _p_capm),
    ("ddm", r"\b(ddm|dividend discount|gordon)\b", _p_ddm),
    ("fcfe", r"\b(fcfe|free cash flow to equity)\b", _p_fcfe),
    ("fcff", r"\b(fcff|free cash flow to (?:the )?firm)\b", _p_fcff),
    ("dupont", r"\b(dupont|du pont)\b", _p_dupont),
    ("debt_to_ebitda", r"\b(debt[- /]to[- /]ebitda|debt/ebitda|leverage ratio)\b", _p_debt_ebitda),
    ("interest_coverage", r"\b(interest coverage|icr)\b", _p_icr),
    ("enterprise_value", r"\b(enterprise value|ev/ebitda|ev to ebitda)\b", _p_ev),
    ("pe_ratio", r"\b(p/?e ratio|price[- ]to[- ]earnings|pe multiple)\b", _p_pe),
    ("real_return", r"\b(real return|real rate|inflation[- ]adjusted)\b", _p_real),
    ("position_size", r"\b(position siz(?:e|ing)|how many shares|quantity to buy)\b", _p_position),
    ("risk_reward", r"\b(risk[- /]?(?:to[- ])?reward|r:r|reward[- ]to[- ]risk)\b", _p_rr),
    ("compound", r"\b(compound interest|compounded|future value|lump ?sum|fixed deposit|\bfd\b)\b", _p_compound),
]

# Concept keys (for conceptual grounding when no numbers are present)
CONCEPT_KEYS: Dict[str, str] = {
    "option_strategy": "option_strategy", "black_scholes": "black_scholes", "bond": "bond_price",
    "cagr": "cagr", "emi": "emi", "sip": "sip", "irr": "irr", "npv": "npv", "wacc": "wacc",
    "capm": "capm", "ddm": "ddm", "fcfe": "fcfe", "fcff": "fcff", "dupont": "dupont",
    "debt_to_ebitda": "debt_to_ebitda", "interest_coverage": "interest_coverage",
    "enterprise_value": "enterprise_value", "pe_ratio": "pe_ratio", "real_return": "real_return",
    "position_size": "position_size", "risk_reward": "risk_reward", "compound": "compound_interest",
}
_EXTRA_CONCEPTS = [
    ("altman_z", r"\baltman|z[- ]score\b"), ("sharpe_sortino", r"\b(sharpe|sortino)\b"),
    ("max_drawdown", r"\bdrawdown\b"), ("ev_ebitda", r"\bev/?ebitda\b"),
]


def detect_concepts(text: str) -> List[str]:
    """Return calculator keys whose definitions are relevant to the query."""
    keys: List[str] = []
    for key, pat, _ in _TRIGGERS:
        if re.search(pat, text, re.I):
            k = CONCEPT_KEYS[key]
            if k not in keys:
                keys.append(k)
    for k, pat in _EXTRA_CONCEPTS:
        if re.search(pat, text, re.I) and k not in keys:
            keys.append(k)
    return keys


def parse(text: str) -> Optional[ParsedCalc]:
    """Best-effort parse. Returns None if the query is not a numeric calculation.

    A query is treated as a calculation only if it matches a trigger AND
    contains at least one number the user wrote.
    """
    if not extract_quantities(text):
        return None
    candidates: List[ParsedCalc] = []
    for _, pat, fn in _TRIGGERS:
        if re.search(pat, text, re.I):
            pc = fn(text)
            if pc.complete:
                return pc
            candidates.append(pc)
    if not candidates:
        return None
    return min(candidates, key=lambda c: len(c.missing))
