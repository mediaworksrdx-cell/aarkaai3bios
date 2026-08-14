import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

def cagr(initial_value: float, final_value: float, years: float) -> float:
    """Compound Annual Growth Rate. Returns percentage."""
    if initial_value <= 0:
        return 0.0
    if years <= 0:
        return 0.0
    try:
        res = (final_value / initial_value) ** (1 / years) - 1
        return res * 100
    except Exception as e:
        logger.error(f"Error in cagr: {e}")
        return 0.0

def absolute_return(buy_price: float, sell_price: float) -> float:
    """Simple percentage return."""
    if buy_price <= 0:
        return 0.0
    return ((sell_price - buy_price) / buy_price) * 100

def annualized_return(total_return_pct: float, holding_days: int) -> float:
    """Annualize a total return over a given number of days."""
    if holding_days <= 0:
        return 0.0
    try:
        # Assuming compound return
        res = (1 + total_return_pct / 100) ** (365 / holding_days) - 1
        return res * 100
    except Exception as e:
        logger.error(f"Error in annualized_return: {e}")
        return 0.0

def sip_future_value(monthly_investment: float, annual_rate_pct: float, years: int) -> dict:
    """SIP calculator. Returns dict with future_value, total_invested, wealth_gained."""
    if monthly_investment <= 0 or years <= 0:
        return {"future_value": 0.0, "total_invested": 0.0, "wealth_gained": 0.0}
    try:
        months = years * 12
        monthly_rate = annual_rate_pct / (12 * 100)
        if monthly_rate == 0:
            fv = monthly_investment * months
        else:
            fv = monthly_investment * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
        
        total_invested = monthly_investment * months
        wealth_gained = fv - total_invested
        return {
            "future_value": round(fv, 2),
            "total_invested": round(total_invested, 2),
            "wealth_gained": round(wealth_gained, 2)
        }
    except Exception as e:
        logger.error(f"Error in sip_future_value: {e}")
        return {"future_value": 0.0, "total_invested": 0.0, "wealth_gained": 0.0}

def lumpsum_future_value(principal: float, annual_rate_pct: float, years: int) -> dict:
    """Lumpsum investment calculator."""
    if principal <= 0 or years <= 0:
        return {"future_value": 0.0, "total_invested": principal, "wealth_gained": 0.0}
    try:
        rate = annual_rate_pct / 100
        fv = principal * (1 + rate) ** years
        wealth_gained = fv - principal
        return {
            "future_value": round(fv, 2),
            "total_invested": round(principal, 2),
            "wealth_gained": round(wealth_gained, 2)
        }
    except Exception as e:
        logger.error(f"Error in lumpsum_future_value: {e}")
        return {"future_value": 0.0, "total_invested": principal, "wealth_gained": 0.0}

def dcf_valuation(free_cash_flows: List[float], discount_rate_pct: float, terminal_growth_pct: float, shares_outstanding: float) -> dict:
    """Discounted Cash Flow valuation. Returns intrinsic_value_per_share, total_pv, terminal_value."""
    if not free_cash_flows or shares_outstanding <= 0:
        return {"intrinsic_value_per_share": 0.0, "total_pv": 0.0, "terminal_value": 0.0}
    try:
        discount_rate = discount_rate_pct / 100
        terminal_growth = terminal_growth_pct / 100
        
        if discount_rate <= terminal_growth:
            return {"intrinsic_value_per_share": 0.0, "total_pv": 0.0, "terminal_value": 0.0}

        pv_fcf = 0.0
        for i, fcf in enumerate(free_cash_flows):
            pv_fcf += fcf / ((1 + discount_rate) ** (i + 1))
        
        last_fcf = free_cash_flows[-1]
        terminal_value = (last_fcf * (1 + terminal_growth)) / (discount_rate - terminal_growth)
        pv_tv = terminal_value / ((1 + discount_rate) ** len(free_cash_flows))
        
        total_pv = pv_fcf + pv_tv
        intrinsic_value_per_share = total_pv / shares_outstanding
        
        return {
            "intrinsic_value_per_share": round(intrinsic_value_per_share, 2),
            "total_pv": round(total_pv, 2),
            "terminal_value": round(terminal_value, 2)
        }
    except Exception as e:
        logger.error(f"Error in dcf_valuation: {e}")
        return {"intrinsic_value_per_share": 0.0, "total_pv": 0.0, "terminal_value": 0.0}

def pe_valuation(eps: float, industry_pe: float, growth_premium: float = 0.0) -> dict:
    """PE-based fair value estimation. Returns fair_value, pe_used."""
    if eps <= 0 or industry_pe <= 0:
        return {"fair_value": 0.0, "pe_used": 0.0}
    try:
        pe_used = industry_pe * (1 + growth_premium / 100)
        fair_value = eps * pe_used
        return {
            "fair_value": round(fair_value, 2),
            "pe_used": round(pe_used, 2)
        }
    except Exception as e:
        logger.error(f"Error in pe_valuation: {e}")
        return {"fair_value": 0.0, "pe_used": 0.0}

def dividend_discount_model(current_dividend: float, growth_rate_pct: float, required_return_pct: float) -> float:
    """Gordon Growth Model — intrinsic value."""
    if current_dividend <= 0:
        return 0.0
    try:
        g = growth_rate_pct / 100
        r = required_return_pct / 100
        if r <= g:
            return 0.0
        d1 = current_dividend * (1 + g)
        iv = d1 / (r - g)
        return round(iv, 2)
    except Exception as e:
        logger.error(f"Error in dividend_discount_model: {e}")
        return 0.0

def risk_reward_ratio(entry_price: float, target_price: float, stoploss_price: float) -> dict:
    """Risk:Reward ratio. Returns risk, reward, ratio, is_favorable."""
    if entry_price <= 0 or target_price <= 0 or stoploss_price <= 0:
        return {"risk": 0.0, "reward": 0.0, "ratio": 0.0, "is_favorable": False}
    try:
        # Assuming long position
        if target_price > entry_price and stoploss_price < entry_price:
            risk = entry_price - stoploss_price
            reward = target_price - entry_price
        # Assuming short position
        elif target_price < entry_price and stoploss_price > entry_price:
            risk = stoploss_price - entry_price
            reward = entry_price - target_price
        else:
            return {"risk": 0.0, "reward": 0.0, "ratio": 0.0, "is_favorable": False}

        if risk == 0:
            return {"risk": 0.0, "reward": 0.0, "ratio": 0.0, "is_favorable": False}

        ratio = reward / risk
        return {
            "risk": round(risk, 2),
            "reward": round(reward, 2),
            "ratio": round(ratio, 2),
            "is_favorable": ratio >= 2.0
        }
    except Exception as e:
        logger.error(f"Error in risk_reward_ratio: {e}")
        return {"risk": 0.0, "reward": 0.0, "ratio": 0.0, "is_favorable": False}

def position_size(total_capital: float, risk_per_trade_pct: float, entry_price: float, stoploss_price: float) -> dict:
    """Position sizing. Returns quantity, risk_amount, position_value."""
    if total_capital <= 0 or risk_per_trade_pct <= 0 or entry_price <= 0 or stoploss_price <= 0 or entry_price == stoploss_price:
        return {"quantity": 0, "risk_amount": 0.0, "position_value": 0.0}
    try:
        risk_amount = total_capital * (risk_per_trade_pct / 100)
        risk_per_share = abs(entry_price - stoploss_price)
        quantity = int(risk_amount // risk_per_share)
        position_value = quantity * entry_price
        return {
            "quantity": quantity,
            "risk_amount": round(risk_amount, 2),
            "position_value": round(position_value, 2)
        }
    except Exception as e:
        logger.error(f"Error in position_size: {e}")
        return {"quantity": 0, "risk_amount": 0.0, "position_value": 0.0}

def margin_required(price: float, lot_size: int, margin_pct: float) -> dict:
    """F&O margin calculator. Returns margin_amount, contract_value."""
    if price <= 0 or lot_size <= 0 or margin_pct <= 0:
        return {"margin_amount": 0.0, "contract_value": 0.0}
    try:
        contract_value = price * lot_size
        margin_amount = contract_value * (margin_pct / 100)
        return {
            "margin_amount": round(margin_amount, 2),
            "contract_value": round(contract_value, 2)
        }
    except Exception as e:
        logger.error(f"Error in margin_required: {e}")
        return {"margin_amount": 0.0, "contract_value": 0.0}

def emi_calculator(principal: float, annual_rate_pct: float, tenure_months: int) -> dict:
    """EMI calculator. Returns emi, total_payment, total_interest."""
    if principal <= 0 or tenure_months <= 0:
        return {"emi": 0.0, "total_payment": 0.0, "total_interest": 0.0}
    try:
        monthly_rate = annual_rate_pct / (12 * 100)
        if monthly_rate == 0:
            emi = principal / tenure_months
        else:
            emi = principal * monthly_rate * ((1 + monthly_rate) ** tenure_months) / (((1 + monthly_rate) ** tenure_months) - 1)
        
        total_payment = emi * tenure_months
        total_interest = total_payment - principal
        return {
            "emi": round(emi, 2),
            "total_payment": round(total_payment, 2),
            "total_interest": round(total_interest, 2)
        }
    except Exception as e:
        logger.error(f"Error in emi_calculator: {e}")
        return {"emi": 0.0, "total_payment": 0.0, "total_interest": 0.0}

def compound_interest(principal: float, annual_rate_pct: float, years: int, compounding_frequency: int = 12) -> dict:
    """Compound interest. Returns final_amount, interest_earned."""
    if principal <= 0 or years <= 0 or compounding_frequency <= 0:
        return {"final_amount": 0.0, "interest_earned": 0.0}
    try:
        rate = annual_rate_pct / 100
        n = compounding_frequency
        final_amount = principal * (1 + rate / n) ** (n * years)
        interest_earned = final_amount - principal
        return {
            "final_amount": round(final_amount, 2),
            "interest_earned": round(interest_earned, 2)
        }
    except Exception as e:
        logger.error(f"Error in compound_interest: {e}")
        return {"final_amount": 0.0, "interest_earned": 0.0}

# ─── Aliases & Tool Compatibility Mappings ──────────────────────────────────
calculate_cagr = cagr
calculate_returns = absolute_return
sip = sip_future_value
calculate_sip = sip_future_value
lumpsum = lumpsum_future_value
dcf = dcf_valuation
pe_value = pe_valuation
ddm = dividend_discount_model
risk_reward = risk_reward_ratio
margin = margin_required
emi = emi_calculator
