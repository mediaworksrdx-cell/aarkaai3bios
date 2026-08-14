import os

finance_add = '''
def get_ohlcv_history(symbol: str, period: str = "1mo", interval: str = "1d") -> dict:
    """Fetch OHLCV candle data via yfinance.
    period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, max
    interval: 1m, 2m, 5m, 15m, 30m, 60m, 90m, 1h, 1d, 5d, 1wk, 1mo
    Returns dict with symbol, period, interval, data (list of candles), stats (high, low, avg_volume)."""
    import yfinance as yf
    try:
        tk = yf.Ticker(symbol)
        hist = tk.history(period=period, interval=interval)
        if hist.empty:
            return {"symbol": symbol, "error": "No data found."}
        data = []
        for index, row in hist.iterrows():
            data.append({
                "date": str(index),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"])
            })
        stats = {
            "high": round(float(hist["High"].max()), 2),
            "low": round(float(hist["Low"].min()), 2),
            "avg_volume": int(hist["Volume"].mean())
        }
        return {"symbol": symbol, "period": period, "interval": interval, "data": data, "stats": stats}
    except Exception as exc:
        logger.error("get_ohlcv_history failed for %s: %s", symbol, exc)
        return {"symbol": symbol, "error": str(exc)}

def get_options_chain(symbol: str) -> dict:
    """Fetch options chain via yfinance. 
    Returns dict with symbol, expiration_dates, calls (list of option data), puts (list),
    summary (total_call_oi, total_put_oi, pcr, max_call_oi_strike, max_put_oi_strike).
    Each option: strike, lastPrice, bid, ask, volume, openInterest, impliedVolatility."""
    import yfinance as yf
    import pandas as pd
    try:
        tk = yf.Ticker(symbol)
        exps = tk.options
        if not exps:
            return {"symbol": symbol, "error": "Options chain not available for this symbol."}
        
        # Get nearest expiry
        chain = tk.option_chain(exps[0])
        calls_df = chain.calls
        puts_df = chain.puts
        
        calls = []
        for _, row in calls_df.iterrows():
            calls.append({
                "strike": float(row.get("strike", 0)),
                "lastPrice": float(row.get("lastPrice", 0)),
                "bid": float(row.get("bid", 0)),
                "ask": float(row.get("ask", 0)),
                "volume": int(row.get("volume", 0) if pd.notna(row.get("volume")) else 0),
                "openInterest": int(row.get("openInterest", 0) if pd.notna(row.get("openInterest")) else 0),
                "impliedVolatility": float(row.get("impliedVolatility", 0))
            })
            
        puts = []
        for _, row in puts_df.iterrows():
            puts.append({
                "strike": float(row.get("strike", 0)),
                "lastPrice": float(row.get("lastPrice", 0)),
                "bid": float(row.get("bid", 0)),
                "ask": float(row.get("ask", 0)),
                "volume": int(row.get("volume", 0) if pd.notna(row.get("volume")) else 0),
                "openInterest": int(row.get("openInterest", 0) if pd.notna(row.get("openInterest")) else 0),
                "impliedVolatility": float(row.get("impliedVolatility", 0))
            })
            
        total_call_oi = sum(c["openInterest"] for c in calls)
        total_put_oi = sum(p["openInterest"] for p in puts)
        pcr = round(total_put_oi / total_call_oi, 2) if total_call_oi > 0 else 0
        
        max_call = max(calls, key=lambda x: x["openInterest"]) if calls else None
        max_put = max(puts, key=lambda x: x["openInterest"]) if puts else None
        
        summary = {
            "total_call_oi": total_call_oi,
            "total_put_oi": total_put_oi,
            "pcr": pcr,
            "max_call_oi_strike": max_call["strike"] if max_call else None,
            "max_put_oi_strike": max_put["strike"] if max_put else None
        }
        
        return {
            "symbol": symbol,
            "expiration_dates": list(exps),
            "calls": calls,
            "puts": puts,
            "summary": summary
        }
    except Exception as exc:
        logger.error("get_options_chain failed for %s: %s", symbol, exc)
        return {"symbol": symbol, "error": str(exc)}

def get_open_interest_summary(symbol: str) -> dict:
    """OI summary from nearest expiry options chain.
    Returns total_call_oi, total_put_oi, pcr, max_pain_estimate, 
    top_call_oi_strikes (top 5), top_put_oi_strikes (top 5)."""
    data = get_options_chain(symbol)
    if "error" in data:
        return data
        
    calls = data.get("calls", [])
    puts = data.get("puts", [])
    
    top_calls = sorted(calls, key=lambda x: x["openInterest"], reverse=True)[:5]
    top_puts = sorted(puts, key=lambda x: x["openInterest"], reverse=True)[:5]
    
    summary = data.get("summary", {})
    
    # Rough max pain estimate
    strikes = set([c["strike"] for c in calls] + [p["strike"] for p in puts])
    max_pain = 0
    min_pain_val = float('inf')
    
    for strike in strikes:
        pain = 0
        for c in calls:
            if c["strike"] < strike:
                pain += (strike - c["strike"]) * c["openInterest"]
        for p in puts:
            if p["strike"] > strike:
                pain += (p["strike"] - strike) * p["openInterest"]
        if pain < min_pain_val:
            min_pain_val = pain
            max_pain = strike
            
    return {
        "symbol": symbol,
        "total_call_oi": summary.get("total_call_oi"),
        "total_put_oi": summary.get("total_put_oi"),
        "pcr": summary.get("pcr"),
        "max_pain_estimate": max_pain,
        "top_call_oi_strikes": [c["strike"] for c in top_calls],
        "top_put_oi_strikes": [p["strike"] for p in top_puts]
    }

def get_stock_info_extended(symbol: str) -> dict:
    """Extended stock info: 52w high/low, avg volume, shares outstanding, 
    float shares, beta, dividend rate, ex-dividend date."""
    import yfinance as yf
    try:
        tk = yf.Ticker(symbol)
        info = tk.info or {}
        return {
            "symbol": symbol,
            "fiftyTwoWeekHigh": info.get("fiftyTwoWeekHigh"),
            "fiftyTwoWeekLow": info.get("fiftyTwoWeekLow"),
            "averageVolume": info.get("averageVolume"),
            "sharesOutstanding": info.get("sharesOutstanding"),
            "floatShares": info.get("floatShares"),
            "beta": info.get("beta"),
            "dividendRate": info.get("dividendRate"),
            "exDividendDate": info.get("exDividendDate")
        }
    except Exception as exc:
        logger.error("get_stock_info_extended failed for %s: %s", symbol, exc)
        return {"symbol": symbol, "error": str(exc)}

def format_ohlcv_context(data: dict) -> str:
    """Format OHLCV data as readable context."""
    if "error" in data:
        return f"OHLCV Data Error for {data.get('symbol')}: {data['error']}"
    
    lines = [f"OHLCV History for {data['symbol']} (Period: {data['period']}, Interval: {data['interval']})"]
    stats = data.get("stats", {})
    lines.append(f"Stats - High: {stats.get('high')}, Low: {stats.get('low')}, Avg Volume: {stats.get('avg_volume')}")
    
    history = data.get("data", [])
    if history:
        lines.append("Recent Candles:")
        for c in history[-5:]: # show last 5
            lines.append(f"  {c['date']}: Open {c['open']}, High {c['high']}, Low {c['low']}, Close {c['close']}, Vol {c['volume']}")
    return "\\n".join(lines)

def format_options_context(data: dict) -> str:
    """Format options chain as readable context."""
    if "error" in data:
        return f"Options Chain Error for {data.get('symbol')}: {data['error']}"
        
    summary = data.get("summary", {})
    return (f"Options Summary for {data['symbol']}:\\n"
            f"Total Call OI: {summary.get('total_call_oi')}\\n"
            f"Total Put OI: {summary.get('total_put_oi')}\\n"
            f"Put/Call Ratio (PCR): {summary.get('pcr')}\\n"
            f"Max Call OI Strike: {summary.get('max_call_oi_strike')}\\n"
            f"Max Put OI Strike: {summary.get('max_put_oi_strike')}")
'''

technical_add = '''
def _sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window=period).mean()

def _adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average Directional Index — trend strength indicator."""
    plus_dm = high.diff()
    minus_dm = low.diff()
    plus_dm[plus_dm < 0] = 0
    minus_dm[minus_dm > 0] = 0
    minus_dm = minus_dm.abs()
    
    # Directional Movement
    plus_dm = plus_dm.where(plus_dm > minus_dm, 0.0)
    minus_dm = minus_dm.where(minus_dm > plus_dm, 0.0)
    
    # True Range
    tr = pd.concat([
        high - low,
        (high - close.shift(1)).abs(),
        (low - close.shift(1)).abs()
    ], axis=1).max(axis=1)
    
    # Wilder's smoothing
    def wilder_smooth(s, n):
        res = pd.Series(index=s.index, dtype=float)
        if len(s) < n:
            return res
        res.iloc[n-1] = s.iloc[:n].sum()
        for i in range(n, len(s)):
            res.iloc[i] = res.iloc[i-1] - (res.iloc[i-1]/n) + s.iloc[i]
        return res
        
    atr = wilder_smooth(tr, period)
    plus_di = 100 * (wilder_smooth(plus_dm, period) / atr)
    minus_di = 100 * (wilder_smooth(minus_dm, period) / atr)
    
    dx = (plus_di - minus_di).abs() / (plus_di + minus_di) * 100
    adx = wilder_smooth(dx, period)
    return adx

def _supertrend(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 10, multiplier: float = 3.0) -> tuple[pd.Series, pd.Series]:
    """Supertrend indicator. Returns (supertrend_line, direction).
    direction: 1 = bullish, -1 = bearish."""
    hl2 = (high + low) / 2
    atr = _atr(high, low, close, period)
    
    upperband = hl2 + (multiplier * atr)
    lowerband = hl2 - (multiplier * atr)
    
    supertrend = pd.Series(index=close.index, dtype=float)
    direction = pd.Series(index=close.index, dtype=int)
    
    for i in range(period, len(close)):
        if close.iloc[i] > upperband.iloc[i-1]:
            direction.iloc[i] = 1
        elif close.iloc[i] < lowerband.iloc[i-1]:
            direction.iloc[i] = -1
        else:
            direction.iloc[i] = direction.iloc[i-1]
            
        if direction.iloc[i] == 1 and lowerband.iloc[i] < lowerband.iloc[i-1]:
            lowerband.iloc[i] = lowerband.iloc[i-1]
        if direction.iloc[i] == -1 and upperband.iloc[i] > upperband.iloc[i-1]:
            upperband.iloc[i] = upperband.iloc[i-1]
            
        if direction.iloc[i] == 1:
            supertrend.iloc[i] = lowerband.iloc[i]
        else:
            supertrend.iloc[i] = upperband.iloc[i]
            
    return supertrend, direction

def _vwap(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
    """Volume Weighted Average Price (intraday cumulative)."""
    typical_price = (high + low + close) / 3
    return (typical_price * volume).cumsum() / volume.cumsum()

def detect_candlestick_patterns(df: pd.DataFrame) -> list[dict]:
    """Detect basic candlestick patterns from OHLC data.
    Patterns: doji, hammer, inverted_hammer, bullish_engulfing, bearish_engulfing,
    morning_star, evening_star, shooting_star.
    Returns list of {pattern, date, signal (bullish/bearish), confidence}."""
    patterns = []
    
    for i in range(2, len(df)):
        O, H, L, C = df['Open'].iloc[i], df['High'].iloc[i], df['Low'].iloc[i], df['Close'].iloc[i]
        O1, H1, L1, C1 = df['Open'].iloc[i-1], df['High'].iloc[i-1], df['Low'].iloc[i-1], df['Close'].iloc[i-1]
        date = str(df.index[i])
        
        body = abs(C - O)
        total_range = H - L
        if total_range == 0: total_range = 0.001
        
        # Doji
        if body <= 0.1 * total_range:
            patterns.append({"pattern": "doji", "date": date, "signal": "neutral", "confidence": 0.5})
            
        # Hammer
        if C > O and (O - L) >= 2 * body and (H - C) <= 0.1 * total_range:
            patterns.append({"pattern": "hammer", "date": date, "signal": "bullish", "confidence": 0.7})
            
        # Bullish Engulfing
        if C1 < O1 and C > O and O <= C1 and C >= O1:
            patterns.append({"pattern": "bullish_engulfing", "date": date, "signal": "bullish", "confidence": 0.8})
            
        # Bearish Engulfing
        if C1 > O1 and C < O and O >= C1 and C <= O1:
            patterns.append({"pattern": "bearish_engulfing", "date": date, "signal": "bearish", "confidence": 0.8})
            
    return patterns

def compute_extended_indicators(symbol: str, period: str = "6mo") -> dict:
    """Compute all indicators including new ones (SMA, ADX, Supertrend, VWAP).
    Returns the existing compute_indicators() dict plus:
    sma_20, sma_50, sma_200, adx, supertrend_value, supertrend_direction, vwap,
    patterns (from detect_candlestick_patterns)."""
    base_data = compute_indicators(symbol, period)
    if not base_data:
        return {}
        
    try:
        import yfinance as yf
        tk = yf.Ticker(symbol)
        hist = tk.history(period=period)
        if hist.empty:
            return base_data
            
        close = hist["Close"]
        high = hist["High"]
        low = hist["Low"]
        volume = hist["Volume"]
        
        sma20 = round(float(_sma(close, 20).iloc[-1]), 2)
        sma50 = round(float(_sma(close, 50).iloc[-1]), 2)
        sma200 = round(float(_sma(close, 200).iloc[-1]), 2) if len(close) >= 200 else None
        
        adx_series = _adx(high, low, close)
        adx_val = round(float(adx_series.iloc[-1]), 2) if not pd.isna(adx_series.iloc[-1]) else None
        
        st, st_dir = _supertrend(high, low, close)
        st_val = round(float(st.iloc[-1]), 2) if not pd.isna(st.iloc[-1]) else None
        st_dir_val = int(st_dir.iloc[-1]) if not pd.isna(st_dir.iloc[-1]) else 0
        
        vwap_series = _vwap(high, low, close, volume)
        vwap_val = round(float(vwap_series.iloc[-1]), 2) if not pd.isna(vwap_series.iloc[-1]) else None
        
        patterns = detect_candlestick_patterns(hist)
        
        extended = {
            "sma_20": sma20,
            "sma_50": sma50,
            "sma_200": sma200,
            "adx": adx_val,
            "supertrend_value": st_val,
            "supertrend_direction": st_dir_val,
            "vwap": vwap_val,
            "patterns": patterns[-5:]  # return last 5 patterns
        }
        
        return {**base_data, **extended}
    except Exception as exc:
        logger.error("compute_extended_indicators failed for %s: %s", symbol, exc)
        return base_data
'''

web_search_add = '''
# Financial news source domains for targeted search
_FINANCIAL_NEWS_DOMAINS = [
    "moneycontrol.com", "economictimes.indiatimes.com", "livemint.com",
    "reuters.com", "bloomberg.com", "cnbcawaaz.com", "ndtvprofit.com",
    "business-standard.com", "financialexpress.com", "thehindubusinessline.com",
    "marketwatch.com", "seekingalpha.com", "investopedia.com"
]

_REGULATORY_DOMAINS = [
    "rbi.org.in", "sebi.gov.in", "mca.gov.in", "nseindia.com", "bseindia.com",
    "pib.gov.in", "incometaxindia.gov.in"
]

def search_financial_news(query: str, max_results: int = 5) -> str:
    """Search financial news from trusted sources.
    Appends financial source domain filters to the search query.
    Returns formatted context with source attribution."""
    domains_query = " OR ".join([f"site:{d}" for d in _FINANCIAL_NEWS_DOMAINS])
    full_query = f"{query} ({domains_query})"
    return get_web_context(full_query, max_results)

def search_regulatory_updates(query: str, max_results: int = 5) -> str:
    """Search RBI/SEBI/MCA regulatory updates.
    Targets government and regulatory domains.
    Returns formatted context with official source links."""
    domains_query = " OR ".join([f"site:{d}" for d in _REGULATORY_DOMAINS])
    full_query = f"{query} ({domains_query})"
    return get_web_context(full_query, max_results)

def search_company_announcements(symbol: str, max_results: int = 5) -> str:
    """Search for recent company announcements, results, board meetings.
    Constructs query from symbol name + 'announcement OR results OR board meeting'.
    Returns formatted results."""
    full_query = f"{symbol} announcement OR results OR board meeting"
    return get_web_context(full_query, max_results)
'''

base_path = r"c:\Users\daarv\.gemini\antigravity\scratch\aarkaai3b\modules"

def append_to_file(filename, text):
    with open(os.path.join(base_path, filename), "a", encoding="utf-8") as f:
        f.write("\n" + text + "\n")

append_to_file("finance.py", finance_add)
append_to_file("technical.py", technical_add)
append_to_file("web_search.py", web_search_add)

print("Appended functions to modules successfully.")
