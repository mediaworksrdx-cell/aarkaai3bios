"""
AARKAAI – Deterministic Finance Formula Engine.

Every function is a pure computation over caller-supplied inputs. There are
no stored answers, no market data and no default economic assumptions (rates,
taxes, volatilities). Model coefficients that are part of a published formula
definition (e.g. Altman Z-Score weights) are kept as named model definitions.

Conventions
-----------
* Rates are decimals (0.12 == 12%).
* Invalid domain inputs raise ``FinanceDomainError`` — never a silent 0.0.
* Each public calculator returns a ``CalcResult`` that carries inputs,
  outputs, intermediate steps and explicit assumptions, so downstream
  components (verifier, renderer) can audit every number.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from typing import Any, Callable, Dict, List, Optional, Sequence


class FinanceDomainError(ValueError):
    """Raised when inputs fall outside a formula's mathematical domain."""


@dataclass
class CalcResult:
    name: str
    formula: str
    inputs: Dict[str, Any]
    outputs: Dict[str, float]
    steps: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)

    def numbers(self) -> List[float]:
        """All numeric values that legitimately appear in this calculation."""
        vals: List[float] = []
        for v in list(self.inputs.values()) + list(self.outputs.values()):
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                vals.append(float(v))
            elif isinstance(v, (list, tuple)):
                vals.extend(float(x) for x in v if isinstance(x, (int, float)))
        return vals


# ───────────────────────────── validation helpers ─────────────────────────────

def _finite(name: str, x: float) -> float:
    try:
        xf = float(x)
    except (TypeError, ValueError) as exc:
        raise FinanceDomainError(f"{name} must be numeric, got {x!r}") from exc
    if not math.isfinite(xf):
        raise FinanceDomainError(f"{name} must be finite, got {x!r}")
    return xf


def _positive(name: str, x: float) -> float:
    xf = _finite(name, x)
    if xf <= 0:
        raise FinanceDomainError(f"{name} must be > 0, got {xf}")
    return xf


def _non_negative(name: str, x: float) -> float:
    xf = _finite(name, x)
    if xf < 0:
        raise FinanceDomainError(f"{name} must be >= 0, got {xf}")
    return xf


def _rate(name: str, x: float) -> float:
    xf = _finite(name, x)
    if xf <= -1.0:
        raise FinanceDomainError(f"{name} must be > -100%, got {xf:.6%}")
    return xf


def _series(name: str, xs: Sequence[float], min_len: int = 1) -> List[float]:
    if xs is None or len(xs) < min_len:
        raise FinanceDomainError(f"{name} requires at least {min_len} values")
    return [_finite(f"{name}[{i}]", v) for i, v in enumerate(xs)]


def _solve_root(f: Callable[[float], float], lo: float, hi: float,
                tol: float = 1e-12, max_iter: int = 500) -> float:
    """Bracketed root finder (bisection with secant acceleration)."""
    flo, fhi = f(lo), f(hi)
    if flo == 0:
        return lo
    if fhi == 0:
        return hi
    if flo * fhi > 0:
        raise FinanceDomainError("No sign change in bracket; root does not exist or is not unique")
    for _ in range(max_iter):
        mid = (lo + hi) / 2.0
        # secant candidate, accepted only if inside bracket
        if fhi != flo:
            sec = hi - fhi * (hi - lo) / (fhi - flo)
            if lo < sec < hi:
                mid = sec if abs(f(sec)) < abs(f((lo + hi) / 2.0)) else (lo + hi) / 2.0
        fm = f(mid)
        if abs(fm) < tol or (hi - lo) / 2.0 < tol:
            return mid
        if flo * fm < 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return (lo + hi) / 2.0


def _expand_bracket(f: Callable[[float], float], lo: float, hi: float,
                    hi_cap: float) -> tuple[float, float]:
    while f(lo) * f(hi) > 0 and hi < hi_cap:
        hi *= 2.0
    return lo, hi


# ─────────────────────────────── growth & returns ─────────────────────────────

def cagr(initial_value: float, final_value: float, years: float) -> CalcResult:
    v0 = _positive("initial_value", initial_value)
    v1 = _non_negative("final_value", final_value)
    n = _positive("years", years)
    ratio = v1 / v0
    root = ratio ** (1.0 / n)
    g = root - 1.0
    return CalcResult(
        "CAGR", "CAGR = (V_final / V_initial)^(1/n) - 1",
        {"initial_value": v0, "final_value": v1, "years": n},
        {"cagr": g, "cagr_pct": g * 100.0, "total_multiple": ratio},
        [f"Multiple = {v1:g} / {v0:g} = {ratio:.6f}",
         f"Root = {ratio:.6f}^(1/{n:g}) = {root:.6f}",
         f"CAGR = {root:.6f} - 1 = {g:.6f} ({g*100:.4f}%)"],
    )


def absolute_return(initial_value: float, final_value: float) -> CalcResult:
    v0 = _positive("initial_value", initial_value)
    v1 = _finite("final_value", final_value)
    r = (v1 - v0) / v0
    return CalcResult("Absolute Return", "R = (V1 - V0) / V0",
                      {"initial_value": v0, "final_value": v1},
                      {"return": r, "return_pct": r * 100.0})


def annualized_return(total_return: float, holding_days: float, days_per_year: float) -> CalcResult:
    tr = _rate("total_return", total_return)
    d = _positive("holding_days", holding_days)
    dpy = _positive("days_per_year", days_per_year)
    a = (1.0 + tr) ** (dpy / d) - 1.0
    return CalcResult("Annualized Return", "R_a = (1 + R)^(D_year / D_held) - 1",
                      {"total_return": tr, "holding_days": d, "days_per_year": dpy},
                      {"annualized_return": a, "annualized_return_pct": a * 100.0})


def real_return(nominal_rate: float, inflation_rate: float) -> CalcResult:
    n = _rate("nominal_rate", nominal_rate)
    i = _rate("inflation_rate", inflation_rate)
    r = (1.0 + n) / (1.0 + i) - 1.0
    return CalcResult("Real Return (Fisher)", "r = (1 + n) / (1 + i) - 1",
                      {"nominal_rate": n, "inflation_rate": i},
                      {"real_rate": r, "real_rate_pct": r * 100.0})


# ─────────────────────────────── time value of money ──────────────────────────

def compound_interest(principal: float, annual_rate: float, years: float,
                      periods_per_year: float) -> CalcResult:
    p = _positive("principal", principal)
    r = _rate("annual_rate", annual_rate)
    t = _non_negative("years", years)
    m = _positive("periods_per_year", periods_per_year)
    fv = p * (1.0 + r / m) ** (m * t)
    return CalcResult("Compound Interest", "FV = P (1 + r/m)^(m t)",
                      {"principal": p, "annual_rate": r, "years": t, "periods_per_year": m},
                      {"future_value": fv, "interest_earned": fv - p})


def lumpsum_future_value(principal: float, annual_rate: float, years: float) -> CalcResult:
    p = _positive("principal", principal)
    r = _rate("annual_rate", annual_rate)
    t = _non_negative("years", years)
    fv = p * (1.0 + r) ** t
    return CalcResult("Lumpsum Future Value", "FV = P (1 + r)^t",
                      {"principal": p, "annual_rate": r, "years": t},
                      {"future_value": fv, "gain": fv - p})


def present_value(future_value: float, rate: float, periods: float) -> CalcResult:
    fv = _finite("future_value", future_value)
    r = _rate("rate", rate)
    n = _non_negative("periods", periods)
    pv = fv / (1.0 + r) ** n
    return CalcResult("Present Value", "PV = FV / (1 + r)^n",
                      {"future_value": fv, "rate": r, "periods": n}, {"present_value": pv})


def sip_future_value(monthly_investment: float, annual_rate: float, years: float,
                     timing: str = "begin") -> CalcResult:
    """SIP FV with monthly compounding. ``timing`` = 'begin' (annuity due) or 'end'."""
    pmt = _positive("monthly_investment", monthly_investment)
    r = _rate("annual_rate", annual_rate)
    t = _positive("years", years)
    if timing not in ("begin", "end"):
        raise FinanceDomainError("timing must be 'begin' or 'end'")
    i = r / 12.0
    n = round(t * 12.0)
    if n <= 0:
        raise FinanceDomainError("SIP horizon must cover at least one month")
    fv = pmt * n if i == 0 else pmt * (((1.0 + i) ** n - 1.0) / i)
    if timing == "begin":
        fv *= (1.0 + i)
    invested = pmt * n
    return CalcResult(
        "SIP Future Value",
        "FV = P [((1+i)^n - 1) / i] (1+i)  [annuity due]" if timing == "begin"
        else "FV = P [((1+i)^n - 1) / i]  [ordinary annuity]",
        {"monthly_investment": pmt, "annual_rate": r, "years": t, "timing": timing},
        {"future_value": fv, "total_invested": invested, "wealth_gained": fv - invested,
         "months": float(n), "monthly_rate": i},
        assumptions=[f"Contributions at the {'beginning' if timing == 'begin' else 'end'} of each month; "
                     "monthly rate = annual rate / 12"],
    )


def emi(principal: float, annual_rate: float, months: float) -> CalcResult:
    p = _positive("principal", principal)
    r = _non_negative("annual_rate", annual_rate)
    n = _positive("months", months)
    i = r / 12.0
    pay = p / n if i == 0 else p * i * (1.0 + i) ** n / ((1.0 + i) ** n - 1.0)
    total = pay * n
    return CalcResult("Loan EMI", "EMI = P i (1+i)^n / ((1+i)^n - 1)",
                      {"principal": p, "annual_rate": r, "months": n},
                      {"emi": pay, "total_payment": total, "total_interest": total - p,
                       "monthly_rate": i})


def npv(rate: float, cash_flows: Sequence[float]) -> CalcResult:
    """NPV with cash_flows[0] at t=0 (undiscounted)."""
    r = _rate("rate", rate)
    cfs = _series("cash_flows", cash_flows, 1)
    pvs = [cf / (1.0 + r) ** t for t, cf in enumerate(cfs)]
    total = sum(pvs)
    return CalcResult("Net Present Value", "NPV = Σ CF_t / (1 + r)^t, t = 0..N",
                      {"rate": r, "cash_flows": cfs}, {"npv": total},
                      [f"t={t}: {cf:g} / (1+{r:g})^{t} = {pv:.4f}" for t, (cf, pv) in enumerate(zip(cfs, pvs))])


def irr(cash_flows: Sequence[float]) -> CalcResult:
    cfs = _series("cash_flows", cash_flows, 2)
    if not (any(c < 0 for c in cfs) and any(c > 0 for c in cfs)):
        raise FinanceDomainError("IRR requires at least one negative and one positive cash flow")
    sign_changes = sum(1 for a, b in zip(cfs, cfs[1:]) if a * b < 0)
    f = lambda r: sum(cf / (1.0 + r) ** t for t, cf in enumerate(cfs))
    lo, hi = _expand_bracket(f, -0.999999, 1.0, 1e6)
    root = _solve_root(f, lo, hi)
    assumptions = []
    if sign_changes > 1:
        assumptions.append(f"{sign_changes} sign changes: multiple IRRs may exist; reporting the root found in (-100%, ∞)")
    return CalcResult("Internal Rate of Return", "Solve Σ CF_t / (1 + IRR)^t = 0",
                      {"cash_flows": cfs}, {"irr": root, "irr_pct": root * 100.0},
                      assumptions=assumptions)


def xirr(cash_flows: Sequence[float], dates: Sequence[date], day_count: float) -> CalcResult:
    cfs = _series("cash_flows", cash_flows, 2)
    if len(dates) != len(cfs):
        raise FinanceDomainError("dates and cash_flows must have equal length")
    dc = _positive("day_count", day_count)
    d0 = min(dates)
    ts = [(d - d0).days / dc for d in dates]
    if not (any(c < 0 for c in cfs) and any(c > 0 for c in cfs)):
        raise FinanceDomainError("XIRR requires both negative and positive cash flows")
    f = lambda r: sum(cf / (1.0 + r) ** t for cf, t in zip(cfs, ts))
    lo, hi = _expand_bracket(f, -0.999999, 1.0, 1e6)
    root = _solve_root(f, lo, hi)
    return CalcResult("XIRR", "Solve Σ CF_i / (1 + r)^((d_i - d_0)/D) = 0",
                      {"cash_flows": cfs, "dates": [str(d) for d in dates], "day_count": dc},
                      {"xirr": root, "xirr_pct": root * 100.0})


def payback_period(cash_flows: Sequence[float]) -> CalcResult:
    cfs = _series("cash_flows", cash_flows, 2)
    cum = 0.0
    for t, cf in enumerate(cfs):
        prev = cum
        cum += cf
        if t > 0 and prev < 0 <= cum:
            frac = -prev / cf
            return CalcResult("Payback Period", "t* where cumulative CF crosses 0 (linear interpolation)",
                              {"cash_flows": cfs}, {"payback_years": (t - 1) + frac})
    raise FinanceDomainError("Cumulative cash flow never turns non-negative; payback not reached")


# ─────────────────────────────── cost of capital & valuation ──────────────────

def capm(risk_free_rate: float, beta: float, market_return: float) -> CalcResult:
    rf = _rate("risk_free_rate", risk_free_rate)
    b = _finite("beta", beta)
    rm = _rate("market_return", market_return)
    ke = rf + b * (rm - rf)
    return CalcResult("CAPM Cost of Equity", "k_e = r_f + β (r_m - r_f)",
                      {"risk_free_rate": rf, "beta": b, "market_return": rm},
                      {"cost_of_equity": ke, "cost_of_equity_pct": ke * 100.0,
                       "equity_risk_premium": rm - rf})


def wacc(equity_value: float, debt_value: float, cost_of_equity: float,
         cost_of_debt: float, tax_rate: float) -> CalcResult:
    e = _non_negative("equity_value", equity_value)
    d = _non_negative("debt_value", debt_value)
    if e + d <= 0:
        raise FinanceDomainError("equity_value + debt_value must be > 0")
    ke = _rate("cost_of_equity", cost_of_equity)
    kd = _rate("cost_of_debt", cost_of_debt)
    t = _finite("tax_rate", tax_rate)
    if not 0 <= t < 1:
        raise FinanceDomainError("tax_rate must be in [0, 1)")
    v = e + d
    w = (e / v) * ke + (d / v) * kd * (1.0 - t)
    return CalcResult("WACC", "WACC = (E/V) k_e + (D/V) k_d (1 - t)",
                      {"equity_value": e, "debt_value": d, "cost_of_equity": ke,
                       "cost_of_debt": kd, "tax_rate": t},
                      {"wacc": w, "wacc_pct": w * 100.0, "weight_equity": e / v, "weight_debt": d / v})


def gordon_growth_value(next_cash_flow: float, discount_rate: float, growth_rate: float) -> CalcResult:
    cf = _finite("next_cash_flow", next_cash_flow)
    r = _rate("discount_rate", discount_rate)
    g = _rate("growth_rate", growth_rate)
    if r <= g:
        raise FinanceDomainError("discount_rate must exceed growth_rate for a finite Gordon value")
    return CalcResult("Gordon Growth Value", "V_0 = CF_1 / (r - g)",
                      {"next_cash_flow": cf, "discount_rate": r, "growth_rate": g},
                      {"value": cf / (r - g)})


def dividend_discount_model(current_dividend: float, growth_rate: float, required_return: float) -> CalcResult:
    d0 = _non_negative("current_dividend", current_dividend)
    g = _rate("growth_rate", growth_rate)
    r = _rate("required_return", required_return)
    if r <= g:
        raise FinanceDomainError("required_return must exceed growth_rate")
    d1 = d0 * (1.0 + g)
    return CalcResult("Dividend Discount Model", "P_0 = D_0 (1 + g) / (r - g)",
                      {"current_dividend": d0, "growth_rate": g, "required_return": r},
                      {"intrinsic_value": d1 / (r - g), "next_dividend": d1})


def dcf_two_stage(base_fcf: float, high_growth_rate: float, high_growth_years: int,
                  terminal_growth_rate: float, discount_rate: float,
                  net_debt: Optional[float] = None, shares_outstanding: Optional[float] = None) -> CalcResult:
    fcf0 = _finite("base_fcf", base_fcf)
    g1 = _rate("high_growth_rate", high_growth_rate)
    n = int(_positive("high_growth_years", high_growth_years))
    gt = _rate("terminal_growth_rate", terminal_growth_rate)
    r = _rate("discount_rate", discount_rate)
    if r <= gt:
        raise FinanceDomainError("discount_rate must exceed terminal_growth_rate")
    steps, pv_sum, fcf = [], 0.0, fcf0
    for t in range(1, n + 1):
        fcf *= (1.0 + g1)
        pv = fcf / (1.0 + r) ** t
        pv_sum += pv
        steps.append(f"Year {t}: FCF={fcf:.4f}, PV={pv:.4f}")
    tv = fcf * (1.0 + gt) / (r - gt)
    pv_tv = tv / (1.0 + r) ** n
    ev = pv_sum + pv_tv
    out = {"enterprise_value": ev, "pv_explicit": pv_sum, "terminal_value": tv, "pv_terminal": pv_tv,
           "terminal_share_of_ev": pv_tv / ev if ev else float("nan")}
    inputs: Dict[str, Any] = {"base_fcf": fcf0, "high_growth_rate": g1, "high_growth_years": n,
                              "terminal_growth_rate": gt, "discount_rate": r}
    if net_debt is not None:
        nd = _finite("net_debt", net_debt)
        inputs["net_debt"] = nd
        out["equity_value"] = ev - nd
        if shares_outstanding is not None:
            sh = _positive("shares_outstanding", shares_outstanding)
            inputs["shares_outstanding"] = sh
            out["value_per_share"] = (ev - nd) / sh
    return CalcResult("Two-Stage DCF (FCFF)",
                      "EV = Σ FCF_t/(1+r)^t + [FCF_n (1+g_T)/(r-g_T)] / (1+r)^n",
                      inputs, out, steps)


def enterprise_value(market_cap: float, total_debt: float, cash: float,
                     preferred_equity: Optional[float] = None,
                     minority_interest: Optional[float] = None) -> CalcResult:
    mc = _non_negative("market_cap", market_cap)
    d = _non_negative("total_debt", total_debt)
    c = _non_negative("cash", cash)
    assumptions = []
    pe = _non_negative("preferred_equity", preferred_equity) if preferred_equity is not None else 0.0
    mi = _non_negative("minority_interest", minority_interest) if minority_interest is not None else 0.0
    if preferred_equity is None:
        assumptions.append("Preferred equity not supplied; excluded from EV")
    if minority_interest is None:
        assumptions.append("Non-controlling interest not supplied; excluded from EV")
    ev = mc + d + pe + mi - c
    return CalcResult("Enterprise Value",
                      "EV = Market Cap + Debt + Preferred + Non-controlling Interest - Cash",
                      {"market_cap": mc, "total_debt": d, "cash": c, "preferred_equity": pe,
                       "minority_interest": mi}, {"enterprise_value": ev}, assumptions=assumptions)


def ev_to_ebitda(enterprise_value_amt: float, ebitda: float) -> CalcResult:
    ev = _finite("enterprise_value", enterprise_value_amt)
    e = _finite("ebitda", ebitda)
    if e == 0:
        raise FinanceDomainError("EBITDA must be non-zero")
    a = [] if e > 0 else ["Negative EBITDA: multiple is not economically meaningful"]
    return CalcResult("EV/EBITDA", "EV / EBITDA", {"enterprise_value": ev, "ebitda": e},
                      {"ev_ebitda": ev / e}, assumptions=a)


def pe_ratio(price: float, eps: float) -> CalcResult:
    p = _positive("price", price)
    e = _finite("eps", eps)
    if e == 0:
        raise FinanceDomainError("EPS must be non-zero")
    a = [] if e > 0 else ["Negative EPS: P/E is not meaningful"]
    return CalcResult("P/E Ratio", "P/E = Price / EPS", {"price": p, "eps": e},
                      {"pe_ratio": p / e, "earnings_yield": e / p}, assumptions=a)


# ─────────────────────────────── cash flows & ratios ──────────────────────────

def fcff(ebit: float, tax_rate: float, depreciation_amortization: float,
         capex: float, change_in_nwc: float) -> CalcResult:
    eb = _finite("ebit", ebit)
    t = _finite("tax_rate", tax_rate)
    if not 0 <= t < 1:
        raise FinanceDomainError("tax_rate must be in [0, 1)")
    da = _finite("depreciation_amortization", depreciation_amortization)
    cx = _finite("capex", capex)
    dn = _finite("change_in_nwc", change_in_nwc)
    v = eb * (1.0 - t) + da - cx - dn
    return CalcResult("FCFF", "FCFF = EBIT(1 - t) + D&A - CapEx - Delta_NWC",
                      {"ebit": eb, "tax_rate": t, "depreciation_amortization": da,
                       "capex": cx, "change_in_nwc": dn}, {"fcff": v, "nopat": eb * (1.0 - t)})


def fcfe_from_fcff(fcff_value: float, interest_expense: float, tax_rate: float,
                   net_borrowing: float) -> CalcResult:
    f = _finite("fcff", fcff_value)
    i = _non_negative("interest_expense", interest_expense)
    t = _finite("tax_rate", tax_rate)
    if not 0 <= t < 1:
        raise FinanceDomainError("tax_rate must be in [0, 1)")
    nb = _finite("net_borrowing", net_borrowing)
    v = f - i * (1.0 - t) + nb
    return CalcResult("FCFE", "FCFE = FCFF - Interest(1 - t) + Net Borrowing",
                      {"fcff": f, "interest_expense": i, "tax_rate": t, "net_borrowing": nb},
                      {"fcfe": v})


def dupont(net_income: float, revenue: float, average_total_assets: float,
           average_equity: float) -> CalcResult:
    ni = _finite("net_income", net_income)
    rev = _positive("revenue", revenue)
    ta = _positive("average_total_assets", average_total_assets)
    eq = _finite("average_equity", average_equity)
    if eq == 0:
        raise FinanceDomainError("average_equity must be non-zero")
    nm, at, em = ni / rev, rev / ta, ta / eq
    a = [] if eq > 0 else ["Negative equity: ROE and equity multiplier are not meaningful"]
    return CalcResult("DuPont ROE (3-step)",
                      "ROE = (NI/Revenue) × (Revenue/Avg Assets) × (Avg Assets/Avg Equity)",
                      {"net_income": ni, "revenue": rev, "average_total_assets": ta, "average_equity": eq},
                      {"net_margin": nm, "asset_turnover": at, "equity_multiplier": em,
                       "roe": nm * at * em, "roe_pct": nm * at * em * 100.0}, assumptions=a)


def debt_to_ebitda(total_debt: float, ebitda: float, cash: Optional[float] = None) -> CalcResult:
    d = _non_negative("total_debt", total_debt)
    e = _finite("ebitda", ebitda)
    if e <= 0:
        raise FinanceDomainError("EBITDA must be > 0 for a meaningful leverage multiple")
    out = {"debt_to_ebitda": d / e}
    inputs: Dict[str, Any] = {"total_debt": d, "ebitda": e}
    if cash is not None:
        c = _non_negative("cash", cash)
        inputs["cash"] = c
        out["net_debt_to_ebitda"] = (d - c) / e
    return CalcResult("Debt / EBITDA", "Debt / EBITDA ; (Debt - Cash) / EBITDA", inputs, out)


def interest_coverage(ebit: float, interest_expense: float) -> CalcResult:
    eb = _finite("ebit", ebit)
    i = _positive("interest_expense", interest_expense)
    return CalcResult("Interest Coverage", "ICR = EBIT / Interest", {"ebit": eb, "interest_expense": i},
                      {"interest_coverage": eb / i})


def economic_value_added(nopat: float, wacc_rate: float, invested_capital: float) -> CalcResult:
    """Economic Value Added (EVA) = NOPAT - (WACC × Invested Capital)."""
    nop = _finite("nopat", nopat)
    w = _rate("wacc_rate", wacc_rate)
    ic = _positive("invested_capital", invested_capital)
    capital_charge = w * ic
    eva_val = nop - capital_charge
    return CalcResult(
        "Economic Value Added (EVA)",
        "EVA = NOPAT - (WACC × Invested Capital)",
        {"nopat": nop, "wacc_rate": w, "invested_capital": ic},
        {"eva": eva_val, "capital_charge": capital_charge, "eva_spread": (nop / ic) - w},
        assumptions=["Capital charge reflects opportunity cost of all invested debt and equity capital"]
    )


def debt_to_equity(interest_bearing_debt: float, shareholders_equity: float, cash: Optional[float] = None) -> CalcResult:
    """Debt-to-Equity Ratio = Total Interest-Bearing Debt / Shareholders' Equity."""
    d = _non_negative("interest_bearing_debt", interest_bearing_debt)
    eq = _finite("shareholders_equity", shareholders_equity)
    if eq == 0:
        raise FinanceDomainError("shareholders_equity must be non-zero")
    de_ratio = d / eq
    out = {"debt_to_equity": de_ratio}
    inputs: Dict[str, Any] = {"interest_bearing_debt": d, "shareholders_equity": eq}
    if cash is not None:
        c = _non_negative("cash", cash)
        inputs["cash"] = c
        out["net_debt_to_equity"] = (d - c) / eq
    return CalcResult(
        "Debt-to-Equity Ratio",
        "D/E = Total Interest-Bearing Debt / Shareholders' Equity ; Net D/E = (Debt - Cash) / Equity",
        inputs,
        out,
        assumptions=["Numerator includes short & long term interest-bearing borrowings; excludes non-debt liabilities like trade payables"]
    )


# Published Altman model definitions (coefficients are part of the model, not data).
ALTMAN_MODELS: Dict[str, Dict[str, Any]] = {
    "original": {
        "label": "Original Z (public manufacturing, 1968)",
        "terms": [("working_capital_to_assets", 1.2), ("retained_earnings_to_assets", 1.4),
                  ("ebit_to_assets", 3.3), ("market_equity_to_liabilities", 0.6),
                  ("sales_to_assets", 1.0)],
        "zones": (1.81, 2.99),
    },
    "private": {
        "label": "Z' (private manufacturing, book equity)",
        "terms": [("working_capital_to_assets", 0.717), ("retained_earnings_to_assets", 0.847),
                  ("ebit_to_assets", 3.107), ("book_equity_to_liabilities", 0.420),
                  ("sales_to_assets", 0.998)],
        "zones": (1.23, 2.90),
    },
    "non_manufacturing": {
        "label": "Z'' (non-manufacturing / emerging markets)",
        "terms": [("working_capital_to_assets", 6.56), ("retained_earnings_to_assets", 3.26),
                  ("ebit_to_assets", 6.72), ("book_equity_to_liabilities", 1.05)],
        "zones": (1.10, 2.60),
    },
}


def altman_z(variant: str, **ratios: float) -> CalcResult:
    if variant not in ALTMAN_MODELS:
        raise FinanceDomainError(f"variant must be one of {sorted(ALTMAN_MODELS)}")
    model = ALTMAN_MODELS[variant]
    missing = [k for k, _ in model["terms"] if k not in ratios]
    if missing:
        raise FinanceDomainError(f"Missing ratios for {variant}: {missing}")
    z, steps = 0.0, []
    for k, w in model["terms"]:
        x = _finite(k, ratios[k])
        z += w * x
        steps.append(f"{w} × {k} ({x:.4f}) = {w * x:.4f}")
    distress, safe = model["zones"]
    zone = "distress" if z < distress else ("safe" if z > safe else "grey")
    return CalcResult(f"Altman {model['label']}",
                      "Z = " + " + ".join(f"{w}·{k}" for k, w in model["terms"]),
                      {"variant": variant, **{k: float(ratios[k]) for k, _ in model["terms"]}},
                      {"z_score": z, "distress_threshold": distress, "safe_threshold": safe},
                      steps, [f"Zone: {zone}"])


# ─────────────────────────────── risk metrics ─────────────────────────────────

def sharpe_sortino(returns: Sequence[float], risk_free_per_period: float,
                   periods_per_year: float, target_return: Optional[float] = None) -> CalcResult:
    rs = _series("returns", returns, 2)
    rf = _finite("risk_free_per_period", risk_free_per_period)
    ppy = _positive("periods_per_year", periods_per_year)
    mar = rf if target_return is None else _finite("target_return", target_return)
    n = len(rs)
    excess = [r - rf for r in rs]
    mean_ex = sum(excess) / n
    var = sum((x - mean_ex) ** 2 for x in excess) / (n - 1)
    sd = math.sqrt(var)
    downside = math.sqrt(sum(min(0.0, r - mar) ** 2 for r in rs) / n)
    mean_vs_mar = sum(r - mar for r in rs) / n
    out = {"mean_excess_return": mean_ex, "std_dev": sd, "downside_deviation": downside,
           "sharpe": (mean_ex / sd) * math.sqrt(ppy) if sd > 0 else float("nan"),
           "sortino": (mean_vs_mar / downside) * math.sqrt(ppy) if downside > 0 else float("nan")}
    return CalcResult("Sharpe & Sortino",
                      "Sharpe = mean(R - r_f)/σ × √P ; Sortino = mean(R - MAR)/DD × √P, DD over all N",
                      {"returns": rs, "risk_free_per_period": rf, "periods_per_year": ppy, "target_return": mar},
                      out, assumptions=["Sample std (N-1) for Sharpe; downside deviation over all N observations"])


def max_drawdown(prices: Sequence[float]) -> CalcResult:
    ps = _series("prices", prices, 2)
    if any(p <= 0 for p in ps):
        raise FinanceDomainError("prices must be > 0")
    peak, mdd = ps[0], 0.0
    for p in ps:
        peak = max(peak, p)
        mdd = min(mdd, p / peak - 1.0)
    return CalcResult("Maximum Drawdown", "MDD = min_t (P_t / max_{s≤t} P_s - 1)",
                      {"prices": ps}, {"max_drawdown": mdd, "max_drawdown_pct": mdd * 100.0})


def position_size(capital: float, risk_fraction: float, entry_price: float, stop_loss: float) -> CalcResult:
    c = _positive("capital", capital)
    rf = _finite("risk_fraction", risk_fraction)
    if not 0 < rf <= 1:
        raise FinanceDomainError("risk_fraction must be in (0, 1]")
    e = _positive("entry_price", entry_price)
    s = _positive("stop_loss", stop_loss)
    per_unit = abs(e - s)
    if per_unit == 0:
        raise FinanceDomainError("entry_price and stop_loss must differ")
    risk_amt = c * rf
    qty = math.floor(risk_amt / per_unit)
    return CalcResult("Position Size", "Qty = floor(Capital × Risk% / |Entry - Stop|)",
                      {"capital": c, "risk_fraction": rf, "entry_price": e, "stop_loss": s},
                      {"quantity": float(qty), "risk_amount": risk_amt, "risk_per_unit": per_unit,
                       "position_value": qty * e})


def risk_reward(entry_price: float, target_price: float, stop_loss: float) -> CalcResult:
    e = _positive("entry_price", entry_price)
    t = _positive("target_price", target_price)
    s = _positive("stop_loss", stop_loss)
    risk, reward = abs(e - s), abs(t - e)
    if risk == 0:
        raise FinanceDomainError("entry_price and stop_loss must differ")
    if (t - e) * (e - s) <= 0:
        raise FinanceDomainError("target and stop must lie on opposite sides of entry")
    return CalcResult("Risk/Reward", "R:R = |Target - Entry| / |Entry - Stop|",
                      {"entry_price": e, "target_price": t, "stop_loss": s},
                      {"reward_to_risk": reward / risk, "risk": risk, "reward": reward,
                       "breakeven_win_rate": risk / (risk + reward)})


# ─────────────────────────────── fixed income ─────────────────────────────────

def bond_price(face_value: float, coupon_rate: float, yield_rate: float, years: float,
               frequency: int) -> CalcResult:
    fv = _positive("face_value", face_value)
    c = _non_negative("coupon_rate", coupon_rate)
    y = _rate("yield_rate", yield_rate)
    t = _positive("years", years)
    m = int(_positive("frequency", frequency))
    n = round(t * m)
    if n <= 0:
        raise FinanceDomainError("bond must have at least one coupon period")
    cpn, i = fv * c / m, y / m
    flows = [(k, cpn + (fv if k == n else 0.0)) for k in range(1, n + 1)]
    price = sum(cf / (1.0 + i) ** k for k, cf in flows)
    mac = sum((k / m) * cf / (1.0 + i) ** k for k, cf in flows) / price
    mod = mac / (1.0 + i)
    conv = sum(k * (k + 1) * cf / (1.0 + i) ** (k + 2) for k, cf in flows) / (price * m * m)
    return CalcResult("Bond Price & Duration", "P = Σ C/(1+y/m)^k + F/(1+y/m)^n",
                      {"face_value": fv, "coupon_rate": c, "yield_rate": y, "years": t, "frequency": m},
                      {"price": price, "macaulay_duration": mac, "modified_duration": mod,
                       "convexity": conv, "coupon_per_period": cpn})


def bond_ytm(price: float, face_value: float, coupon_rate: float, years: float, frequency: int) -> CalcResult:
    p = _positive("price", price)
    f = lambda y: bond_price(face_value, coupon_rate, y, years, frequency).outputs["price"] - p
    lo, hi = _expand_bracket(f, -0.99 * frequency + 1e-9 if frequency else -0.99, 1.0, 1e3)
    y = _solve_root(f, lo, hi)
    return CalcResult("Bond Yield to Maturity", "Solve P = Σ C/(1+y/m)^k + F/(1+y/m)^n for y",
                      {"price": p, "face_value": float(face_value), "coupon_rate": float(coupon_rate),
                       "years": float(years), "frequency": float(frequency)},
                      {"ytm": y, "ytm_pct": y * 100.0})


# ─────────────────────────────── options ──────────────────────────────────────

def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def _norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def black_scholes(spot: float, strike: float, time_years: float, risk_free_rate: float,
                  volatility: float, option_type: str, dividend_yield: float = 0.0) -> CalcResult:
    """Black-Scholes-Merton. ``dividend_yield`` defaults to 0 (no carry) and is reported."""
    s = _positive("spot", spot)
    k = _positive("strike", strike)
    t = _positive("time_years", time_years)
    r = _finite("risk_free_rate", risk_free_rate)
    v = _positive("volatility", volatility)
    q = _finite("dividend_yield", dividend_yield)
    ot = option_type.lower()
    if ot not in ("call", "put"):
        raise FinanceDomainError("option_type must be 'call' or 'put'")
    sq = math.sqrt(t)
    d1 = (math.log(s / k) + (r - q + 0.5 * v * v) * t) / (v * sq)
    d2 = d1 - v * sq
    dq, dr = math.exp(-q * t), math.exp(-r * t)
    if ot == "call":
        price = s * dq * _norm_cdf(d1) - k * dr * _norm_cdf(d2)
        delta = dq * _norm_cdf(d1)
        theta = (-s * dq * _norm_pdf(d1) * v / (2 * sq) - r * k * dr * _norm_cdf(d2) + q * s * dq * _norm_cdf(d1))
        rho = k * t * dr * _norm_cdf(d2)
    else:
        price = k * dr * _norm_cdf(-d2) - s * dq * _norm_cdf(-d1)
        delta = -dq * _norm_cdf(-d1)
        theta = (-s * dq * _norm_pdf(d1) * v / (2 * sq) + r * k * dr * _norm_cdf(-d2) - q * s * dq * _norm_cdf(-d1))
        rho = -k * t * dr * _norm_cdf(-d2)
    gamma = dq * _norm_pdf(d1) / (s * v * sq)
    vega = s * dq * _norm_pdf(d1) * sq
    return CalcResult("Black-Scholes-Merton",
                      "C = S e^{-qT} N(d1) - K e^{-rT} N(d2); P = K e^{-rT} N(-d2) - S e^{-qT} N(-d1)",
                      {"spot": s, "strike": k, "time_years": t, "risk_free_rate": r, "volatility": v,
                       "option_type": ot, "dividend_yield": q},
                      {"price": price, "d1": d1, "d2": d2, "delta": delta, "gamma": gamma,
                       "vega_per_1pct": vega / 100.0, "theta_per_day": theta / 365.0, "rho_per_1pct": rho / 100.0},
                      assumptions=["European exercise; constant volatility and rates; theta per calendar day"])


def implied_volatility(market_price: float, spot: float, strike: float, time_years: float,
                       risk_free_rate: float, option_type: str, dividend_yield: float = 0.0) -> CalcResult:
    mp = _positive("market_price", market_price)
    f = lambda vol: black_scholes(spot, strike, time_years, risk_free_rate, vol, option_type,
                                  dividend_yield).outputs["price"] - mp
    lo, hi = 1e-6, 1.0
    lo, hi = _expand_bracket(f, lo, hi, 64.0)
    iv = _solve_root(f, lo, hi, tol=1e-10)
    return CalcResult("Implied Volatility", "Solve BS(σ) = market price",
                      {"market_price": mp, "spot": float(spot), "strike": float(strike),
                       "time_years": float(time_years), "risk_free_rate": float(risk_free_rate),
                       "option_type": option_type}, {"implied_volatility": iv, "implied_volatility_pct": iv * 100})


def option_strategy_payoff(legs: Sequence[Dict[str, Any]]) -> CalcResult:
    """Expiry payoff for a multi-leg strategy.

    Each leg: {"type": "call"|"put", "strike": K, "premium": p, "quantity": q}
    with q > 0 long, q < 0 short. Max profit/loss and breakevens are derived
    exactly from the piecewise-linear payoff (evaluated at kinks and tails).
    """
    if not legs:
        raise FinanceDomainError("at least one leg required")
    parsed = []
    for i, lg in enumerate(legs):
        typ = str(lg.get("type", "")).lower()
        if typ not in ("call", "put"):
            raise FinanceDomainError(f"leg {i}: type must be call/put")
        parsed.append((typ, _positive(f"leg{i}.strike", lg["strike"]),
                       _non_negative(f"leg{i}.premium", lg["premium"]),
                       _finite(f"leg{i}.quantity", lg["quantity"])))

    def pnl(s: float) -> float:
        tot = 0.0
        for typ, k, prem, q in parsed:
            intrinsic = max(0.0, s - k) if typ == "call" else max(0.0, k - s)
            tot += q * (intrinsic - prem)
        return tot

    strikes = sorted({k for _, k, _, _ in parsed})
    pts = [0.0] + strikes
    vals = [pnl(x) for x in pts]
    slope_up = sum(q for typ, _, _, q in parsed if typ == "call")
    net_premium = -sum(q * prem for _, _, prem, q in parsed)
    max_profit = float("inf") if slope_up > 0 else max(vals + [pnl(strikes[-1])])
    max_loss = float("-inf") if slope_up < 0 else min(vals)
    breakevens: List[float] = []
    for (a, fa), (b, fb) in zip(zip(pts, vals), zip(pts[1:], vals[1:])):
        if fa == 0 and a not in breakevens:
            breakevens.append(a)
        elif fa * fb < 0:
            breakevens.append(a + (b - a) * (-fa) / (fb - fa))
    last, flast = pts[-1], vals[-1]
    if slope_up != 0 and flast * slope_up < 0:
        breakevens.append(last - flast / slope_up)
    return CalcResult("Option Strategy Payoff at Expiry", "Σ q_i (intrinsic_i(S_T) - premium_i)",
                      {"legs": [{"type": t, "strike": k, "premium": p, "quantity": q} for t, k, p, q in parsed]},
                      {"net_premium": net_premium, "max_profit": max_profit, "max_loss": max_loss,
                       **{f"breakeven_{i+1}": b for i, b in enumerate(breakevens)}},
                      [f"P&L at S={x:g}: {v:.4f}" for x, v in zip(pts, vals)],
                      ["net_premium > 0 means net credit received"])


# ─────────────────────────────── registry ─────────────────────────────────────

CALCULATORS: Dict[str, Callable[..., CalcResult]] = {
    "cagr": cagr, "absolute_return": absolute_return, "annualized_return": annualized_return,
    "real_return": real_return, "compound_interest": compound_interest,
    "lumpsum": lumpsum_future_value, "present_value": present_value, "sip": sip_future_value,
    "emi": emi, "npv": npv, "irr": irr, "xirr": xirr, "payback": payback_period,
    "capm": capm, "wacc": wacc, "gordon": gordon_growth_value, "ddm": dividend_discount_model,
    "dcf": dcf_two_stage, "enterprise_value": enterprise_value, "ev_ebitda": ev_to_ebitda,
    "pe_ratio": pe_ratio, "fcff": fcff, "fcfe": fcfe_from_fcff, "dupont": dupont,
    "debt_to_ebitda": debt_to_ebitda, "interest_coverage": interest_coverage, "altman_z": altman_z,
    "eva": economic_value_added, "debt_to_equity": debt_to_equity,
    "sharpe_sortino": sharpe_sortino, "max_drawdown": max_drawdown, "position_size": position_size,
    "risk_reward": risk_reward, "bond_price": bond_price, "bond_ytm": bond_ytm,
    "black_scholes": black_scholes, "implied_volatility": implied_volatility,
    "option_strategy": option_strategy_payoff,
}


def calculate(name: str, **kwargs: Any) -> CalcResult:
    if name not in CALCULATORS:
        raise FinanceDomainError(f"Unknown calculator '{name}'. Available: {sorted(CALCULATORS)}")
    return CALCULATORS[name](**kwargs)


def _altman_definitions() -> str:
    return (
        "Original Z (1968 public manufacturing): Z = 1.2(WC/TA) + 1.4(RE/TA) + 3.3(EBIT/TA) + 0.6(MVE/TL) + 0.999(Sales/TA) "
        "(or 1.0); distress < 1.81, safe > 2.99 | "
        "Z' (private manufacturing): Z' = 0.717 X1 + 0.847 X2 + 3.107 X3 + 0.420 X4 + 0.998 X5 | "
        "Z'' (non-manufacturing / emerging markets): Z'' = 6.56 X1 + 3.26 X2 + 6.72 X3 + 1.05 X4"
    )


# Canonical definitions used to ground conceptual (no-number) explanations.
FORMULAS: Dict[str, str] = {
    "cagr": "CAGR = (V_final / V_initial)^(1/n) - 1",
    "npv": "NPV = Σ CF_t / (1 + r)^t, t = 0..N",
    "irr": "IRR solves Σ CF_t / (1 + IRR)^t = 0",
    "xirr": "XIRR solves Σ CF_i / (1 + r)^((d_i - d_0)/365) = 0",
    "capm": "k_e = r_f + β (r_m - r_f)",
    "wacc": "WACC = (E/V) k_e + (D/V) k_d (1 - t)",
    "ddm": "P_0 = D_0 (1 + g) / (r - g), requires r > g",
    "gordon": "V_0 = CF_1 / (r - g), requires r > g",
    "dcf": "EV = Σ FCFF_t/(1+WACC)^t + TV/(1+WACC)^n ; TV = FCFF_{n+1}/(WACC - g)",
    "enterprise_value": "EV = Market Cap + Total Debt + Preferred Equity + Non-controlling Interest - Cash & Equivalents",
    "ev_ebitda": "EV/EBITDA = Enterprise Value / EBITDA",
    "pe_ratio": "P/E = Share Price / EPS",
    "fcff": "FCFF = EBIT(1 - t) + D&A - CapEx - Delta_NWC",
    "fcfe": "FCFE = FCFF - Interest(1 - t) + Net Borrowing = NI + D&A - CapEx - Delta_NWC + Net Borrowing",
    "dupont": "ROE = Net Margin (NI/Revenue) × Asset Turnover (Revenue/Avg Assets) × Equity Multiplier (Avg Assets/Avg Equity)",
    "debt_to_ebitda": "Debt/EBITDA = Total Debt / EBITDA ; Net Debt/EBITDA = (Debt - Cash) / EBITDA",
    "debt_to_equity": "D/E = Total Interest-Bearing Debt / Shareholders' Equity ; Net D/E = (Debt - Cash) / Equity",
    "eva": "EVA = NOPAT - (WACC × Invested Capital) ; Capital Charge = WACC × Invested Capital",
    "interest_coverage": "ICR = EBIT / Interest Expense",
    "altman_z": _altman_definitions(),
    "sharpe_sortino": "Sharpe = mean(R - r_f)/σ × √P ; Sortino = mean(R - MAR)/DownsideDev × √P (DownsideDev over all N)",
    "max_drawdown": "MDD = min_t (P_t / running_peak_t - 1)",
    "emi": "EMI = P i (1+i)^n / ((1+i)^n - 1), i = annual rate / 12",
    "sip": "FV = P [((1+i)^n - 1)/i] (1+i), i = annual rate / 12 (contributions at period start)",
    "compound_interest": "FV = P (1 + r/m)^(m t)",
    "real_return": "Real = (1 + nominal) / (1 + inflation) - 1",
    "bond_price": "P = Σ C/(1+y/m)^k + F/(1+y/m)^n ; ModDur = MacDur / (1 + y/m)",
    "bond_ytm": "YTM solves P = Σ C/(1+y/m)^k + F/(1+y/m)^n",
    "black_scholes": "C = S e^{-qT} N(d1) - K e^{-rT} N(d2); d1 = [ln(S/K) + (r - q + σ²/2)T]/(σ√T); d2 = d1 - σ√T",
    "position_size": "Quantity = floor(Capital × Risk% / |Entry - Stop|)",
    "risk_reward": "R:R = |Target - Entry| / |Entry - Stop| ; breakeven win rate = 1 / (1 + R:R)",
    "option_strategy": ("Bull call spread: long lower-K call + short higher-K call, max loss = net debit, "
                        "max profit = width - debit. Bear put spread: long higher-K put + short lower-K put, "
                        "max loss = net debit, max profit = width - debit. Iron condor: long put K1 < short put K2 "
                        "< short call K3 < long call K4, max profit = net credit, max loss = wider wing - credit."),
}


def formula_reference(name: str) -> Optional[str]:
    """Return the canonical formula definition string for a calculator, if known."""
    return FORMULAS.get(name)
