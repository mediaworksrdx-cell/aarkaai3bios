import numpy as np
from scipy.stats import norm
import logging

logger = logging.getLogger(__name__)

def black_scholes_price(spot: float, strike: float, time_to_expiry: float, risk_free_rate: float, volatility: float, option_type: str = "call") -> float:
    """Black-Scholes option price. time_to_expiry in years."""
    if time_to_expiry <= 0 or volatility <= 0:
        return max(0.0, spot - strike) if option_type == "call" else max(0.0, strike - spot)

    d1 = (np.log(spot / strike) + (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry) / (volatility * np.sqrt(time_to_expiry))
    d2 = d1 - volatility * np.sqrt(time_to_expiry)

    if option_type.lower() == "call":
        price = spot * norm.cdf(d1) - strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(d2)
    elif option_type.lower() == "put":
        price = strike * np.exp(-risk_free_rate * time_to_expiry) * norm.cdf(-d2) - spot * norm.cdf(-d1)
    else:
        raise ValueError("option_type must be 'call' or 'put'")

    return float(max(0.0, price))

def compute_greeks(spot: float, strike: float, time_to_expiry: float, risk_free_rate: float, volatility: float, option_type: str = "call") -> dict:
    """Full Greeks: delta, gamma, theta, vega, rho.
    All properly annualized. Handle edge cases (expiry=0, vol=0)."""
    if time_to_expiry <= 0 or volatility <= 0:
        return {
            "delta": 1.0 if option_type == "call" and spot > strike else (-1.0 if option_type == "put" and spot < strike else 0.0),
            "gamma": 0.0,
            "theta": 0.0,
            "vega": 0.0,
            "rho": 0.0
        }

    d1 = (np.log(spot / strike) + (risk_free_rate + 0.5 * volatility ** 2) * time_to_expiry) / (volatility * np.sqrt(time_to_expiry))
    d2 = d1 - volatility * np.sqrt(time_to_expiry)

    pdf_d1 = norm.pdf(d1)
    cdf_d1 = norm.cdf(d1)
    cdf_neg_d1 = norm.cdf(-d1)
    cdf_d2 = norm.cdf(d2)
    cdf_neg_d2 = norm.cdf(-d2)

    gamma = pdf_d1 / (spot * volatility * np.sqrt(time_to_expiry))
    vega = spot * pdf_d1 * np.sqrt(time_to_expiry) / 100.0  # Per 1% vol

    if option_type.lower() == "call":
        delta = cdf_d1
        theta = (- (spot * pdf_d1 * volatility) / (2 * np.sqrt(time_to_expiry)) 
                 - risk_free_rate * strike * np.exp(-risk_free_rate * time_to_expiry) * cdf_d2) / 365.0
        rho = strike * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry) * cdf_d2 / 100.0
    elif option_type.lower() == "put":
        delta = cdf_d1 - 1
        theta = (- (spot * pdf_d1 * volatility) / (2 * np.sqrt(time_to_expiry)) 
                 + risk_free_rate * strike * np.exp(-risk_free_rate * time_to_expiry) * cdf_neg_d2) / 365.0
        rho = -strike * time_to_expiry * np.exp(-risk_free_rate * time_to_expiry) * cdf_neg_d2 / 100.0
    else:
        raise ValueError("option_type must be 'call' or 'put'")

    return {
        "delta": float(delta),
        "gamma": float(gamma),
        "theta": float(theta),
        "vega": float(vega),
        "rho": float(rho)
    }

def compute_implied_volatility(option_price: float, spot: float, strike: float, time_to_expiry: float, risk_free_rate: float, option_type: str = "call") -> float:
    """Newton-Raphson IV solver. Max 100 iterations, tolerance 1e-6."""
    MAX_ITER = 100
    TOLERANCE = 1e-6
    sigma = 0.5  # initial guess

    for i in range(MAX_ITER):
        price = black_scholes_price(spot, strike, time_to_expiry, risk_free_rate, sigma, option_type)
        vega = compute_greeks(spot, strike, time_to_expiry, risk_free_rate, sigma, option_type)["vega"] * 100.0 # scale back vega
        
        diff = price - option_price
        
        if abs(diff) < TOLERANCE:
            return float(sigma)
            
        if vega < 1e-6: # avoid division by zero
            break
            
        sigma = sigma - diff / vega
        
        if sigma <= 0.0:
            sigma = 0.001

    return float(sigma)

def compute_max_pain(options_chain: dict) -> dict:
    """Max Pain calculation from options chain data.
    options_chain: {strike: {call_oi: int, put_oi: int}}
    Returns max_pain_strike, total_pain_at_max_pain, pain_distribution."""
    pain_dist = {}
    strikes = sorted([float(k) for k in options_chain.keys()])
    
    if not strikes:
        return {"max_pain_strike": 0.0, "total_pain_at_max_pain": 0.0, "pain_distribution": {}}
        
    for current_strike in strikes:
        total_pain = 0.0
        for strike in strikes:
            call_oi = options_chain[strike].get("call_oi", 0)
            put_oi = options_chain[strike].get("put_oi", 0)
            
            # Call sellers lose if current_strike > strike
            if current_strike > strike:
                total_pain += (current_strike - strike) * call_oi
                
            # Put sellers lose if current_strike < strike
            if current_strike < strike:
                total_pain += (strike - current_strike) * put_oi
                
        pain_dist[current_strike] = total_pain
        
    max_pain_strike = min(pain_dist, key=pain_dist.get)
    return {
        "max_pain_strike": max_pain_strike,
        "total_pain_at_max_pain": pain_dist[max_pain_strike],
        "pain_distribution": pain_dist
    }

def compute_pcr(options_chain: dict) -> dict:
    """Put-Call Ratio from OI data."""
    total_put_oi = sum(v.get("put_oi", 0) for v in options_chain.values())
    total_call_oi = sum(v.get("call_oi", 0) for v in options_chain.values())
    total_put_vol = sum(v.get("put_volume", 0) for v in options_chain.values())
    total_call_vol = sum(v.get("call_volume", 0) for v in options_chain.values())

    pcr_oi = total_put_oi / total_call_oi if total_call_oi > 0 else 0.0
    pcr_vol = total_put_vol / total_call_vol if total_call_vol > 0 else 0.0

    interpretation = "Neutral"
    if pcr_oi > 1.2:
        interpretation = "Oversold / Bullish"
    elif pcr_oi < 0.6:
        interpretation = "Overbought / Bearish"

    return {
        "pcr_oi": pcr_oi,
        "pcr_volume": pcr_vol,
        "interpretation": interpretation
    }

def compute_iv_percentile(iv_history: list[float], current_iv: float) -> dict:
    """IV percentile and rank."""
    if not iv_history:
        return {"iv_percentile": 0.0, "iv_rank": 0.0, "current_iv": current_iv, "median_iv": current_iv, "interpretation": "No history"}
        
    iv_history = [v for v in iv_history if v is not None and not np.isnan(v)]
    if not iv_history:
        return {"iv_percentile": 0.0, "iv_rank": 0.0, "current_iv": current_iv, "median_iv": current_iv, "interpretation": "No valid history"}

    min_iv = min(iv_history)
    max_iv = max(iv_history)
    median_iv = float(np.median(iv_history))

    iv_rank = ((current_iv - min_iv) / (max_iv - min_iv) * 100.0) if max_iv > min_iv else 0.0
    
    count_below = sum(1 for v in iv_history if v < current_iv)
    iv_percentile = (count_below / len(iv_history)) * 100.0

    interpretation = "Neutral"
    if iv_percentile > 80:
        interpretation = "High IV - Premium Selling Favored"
    elif iv_percentile < 20:
        interpretation = "Low IV - Premium Buying Favored"

    return {
        "iv_percentile": iv_percentile,
        "iv_rank": iv_rank,
        "current_iv": current_iv,
        "median_iv": median_iv,
        "interpretation": interpretation
    }

def oi_analysis(options_chain: dict, previous_chain: dict = None) -> dict:
    """OI analysis: max call OI strike (resistance), max put OI strike (support)."""
    if not options_chain:
        return {}

    max_call_strike = max(options_chain.keys(), key=lambda k: options_chain[k].get("call_oi", 0))
    max_put_strike = max(options_chain.keys(), key=lambda k: options_chain[k].get("put_oi", 0))
    
    analysis = {
        "resistance_strike": float(max_call_strike),
        "resistance_oi": options_chain[max_call_strike].get("call_oi", 0),
        "support_strike": float(max_put_strike),
        "support_oi": options_chain[max_put_strike].get("put_oi", 0),
    }

    if previous_chain:
        call_change = options_chain[max_call_strike].get("call_oi", 0) - previous_chain.get(max_call_strike, {}).get("call_oi", 0)
        put_change = options_chain[max_put_strike].get("put_oi", 0) - previous_chain.get(max_put_strike, {}).get("put_oi", 0)
        analysis["resistance_oi_change"] = call_change
        analysis["support_oi_change"] = put_change
        
    return analysis

def format_greeks_context(greeks: dict) -> str:
    """Format Greeks as readable context string."""
    return f"Delta: {greeks.get('delta', 0):.4f} | Gamma: {greeks.get('gamma', 0):.4f} | Theta: {greeks.get('theta', 0):.4f} | Vega: {greeks.get('vega', 0):.4f} | Rho: {greeks.get('rho', 0):.4f}"

def format_fno_analysis_context(analysis: dict) -> str:
    """Format F&O analysis as readable context string."""
    parts = []
    if "pcr_oi" in analysis:
        parts.append(f"PCR (OI): {analysis['pcr_oi']:.2f} ({analysis.get('interpretation', '')})")
    if "max_pain_strike" in analysis:
        parts.append(f"Max Pain Strike: {analysis['max_pain_strike']}")
    if "resistance_strike" in analysis:
        parts.append(f"Support (Max Put OI): {analysis['support_strike']} | Resistance (Max Call OI): {analysis['resistance_strike']}")
    return " | ".join(parts)
