"""
AARKAAI – Finance Module (yfinance)

Supports: US / India stocks, crypto, commodities, forex.
Only triggered when the semantic filter routes a finance query.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

import yfinance as yf

from config import COMMODITY_TICKERS, CRYPTO_SUFFIXES, FOREX_PAIRS, INDIA_SUFFIX

logger = logging.getLogger(__name__)

# ─── Common US tickers for quick lookup ───────────────────────────────────────
_US_TICKERS: dict[str, str] = {
    # FAANG / Magnificent 7
    "apple": "AAPL", "google": "GOOGL", "alphabet": "GOOGL",
    "microsoft": "MSFT", "amazon": "AMZN", "meta": "META", "facebook": "META",
    "tesla": "TSLA", "nvidia": "NVDA",
    # Semiconductors
    "amd": "AMD", "intel": "INTC", "qualcomm": "QCOM", "broadcom": "AVGO",
    "texas instruments": "TXN", "micron": "MU", "arm": "ARM", "tsmc": "TSM",
    # Software / Cloud
    "salesforce": "CRM", "adobe": "ADBE", "oracle": "ORCL", "servicenow": "NOW",
    "snowflake": "SNOW", "palantir": "PLTR", "crowdstrike": "CRWD",
    "datadog": "DDOG", "twilio": "TWLO", "shopify": "SHOP", "spotify": "SPOT",
    # Social / Media / Entertainment
    "netflix": "NFLX", "disney": "DIS", "snap": "SNAP", "pinterest": "PINS",
    "uber": "UBER", "airbnb": "ABNB", "doordash": "DASH", "roblox": "RBLX",
    # Finance / Banks
    "jpmorgan": "JPM", "jp morgan": "JPM", "goldman sachs": "GS", "goldman": "GS",
    "morgan stanley": "MS", "bank of america": "BAC", "wells fargo": "WFC",
    "citigroup": "C", "visa": "V", "mastercard": "MA", "paypal": "PYPL",
    "american express": "AXP", "amex": "AXP", "square": "XYZ", "block": "XYZ",
    "charles schwab": "SCHW", "blackrock": "BLK", "berkshire": "BRK-B",
    # Healthcare / Pharma
    "johnson & johnson": "JNJ", "j&j": "JNJ", "pfizer": "PFE",
    "unitedhealth": "UNH", "abbvie": "ABBV", "merck": "MRK", "eli lilly": "LLY",
    "moderna": "MRNA", "amgen": "AMGN", "gilead": "GILD", "novo nordisk": "NVO",
    # Energy
    "exxon": "XOM", "exxonmobil": "XOM", "chevron": "CVX", "shell": "SHEL",
    "conocophillips": "COP", "bp": "BP", "schlumberger": "SLB",
    # Consumer / Retail
    "walmart": "WMT", "costco": "COST", "home depot": "HD", "target": "TGT",
    "coca-cola": "KO", "coke": "KO", "pepsi": "PEP", "pepsico": "PEP",
    "procter & gamble": "PG", "p&g": "PG", "nike": "NKE", "starbucks": "SBUX",
    "mcdonald": "MCD", "mcdonalds": "MCD",
    # Industrial / Aerospace
    "boeing": "BA", "lockheed": "LMT", "caterpillar": "CAT", "3m": "MMM",
    "honeywell": "HON", "general electric": "GE", "ge": "GE",
    # Telecom
    "at&t": "T", "att": "T", "verizon": "VZ", "t-mobile": "TMUS",
    # Auto / EV
    "ford": "F", "gm": "GM", "general motors": "GM",
    "rivian": "RIVN", "lucid": "LCID", "nio": "NIO",
    # IBM / Legacy Tech
    "ibm": "IBM", "cisco": "CSCO", "hp": "HPQ", "dell": "DELL",
}

_INDIA_TICKERS: dict[str, str] = {
    # Nifty 50 components (top companies)
    "reliance": "RELIANCE.NS", "ril": "RELIANCE.NS",
    "tcs": "TCS.NS", "tata consultancy": "TCS.NS",
    "infosys": "INFY.NS", "infy": "INFY.NS",
    "hdfc bank": "HDFCBANK.NS", "hdfc": "HDFCBANK.NS", "hdfcbank": "HDFCBANK.NS",
    "icici bank": "ICICIBANK.NS", "icici": "ICICIBANK.NS",
    "sbi": "SBIN.NS", "state bank": "SBIN.NS", "state bank of india": "SBIN.NS",
    "wipro": "WIPRO.NS",
    "hcl": "HCLTECH.NS", "hcl tech": "HCLTECH.NS", "hcltech": "HCLTECH.NS",
    "airtel": "BHARTIARTL.NS", "bharti airtel": "BHARTIARTL.NS",
    "itc": "ITC.NS",
    "kotak": "KOTAKBANK.NS", "kotak mahindra": "KOTAKBANK.NS", "kotak bank": "KOTAKBANK.NS",
    "lt": "LT.NS", "larsen": "LT.NS", "larsen & toubro": "LT.NS",
    "hul": "HINDUNILVR.NS", "hindustan unilever": "HINDUNILVR.NS",
    "bajaj finance": "BAJFINANCE.NS", "bajaj": "BAJFINANCE.NS", "bajfinance": "BAJFINANCE.NS",
    "bajaj finserv": "BAJAJFINSV.NS",
    "maruti": "MARUTI.NS", "maruti suzuki": "MARUTI.NS",
    "tata motors": "TMPV.NS", "tatamotors": "TMPV.NS",
    "tata steel": "TATASTEEL.NS", "tatasteel": "TATASTEEL.NS",
    "sunpharma": "SUNPHARMA.NS", "sun pharma": "SUNPHARMA.NS",
    "titan": "TITAN.NS",
    "asian paints": "ASIANPAINT.NS", "asianpaint": "ASIANPAINT.NS",
    "ultratech": "ULTRACEMCO.NS", "ultratech cement": "ULTRACEMCO.NS",
    "power grid": "POWERGRID.NS", "powergrid": "POWERGRID.NS",
    "ntpc": "NTPC.NS",
    "ongc": "ONGC.NS",
    "coal india": "COALINDIA.NS", "coalindia": "COALINDIA.NS",
    "grasim": "GRASIM.NS",
    "nestle india": "NESTLEIND.NS", "nestle": "NESTLEIND.NS",
    "britannia": "BRITANNIA.NS",
    "divis": "DIVISLAB.NS", "divis lab": "DIVISLAB.NS",
    "dr reddy": "DRREDDY.NS", "drreddy": "DRREDDY.NS",
    "cipla": "CIPLA.NS",
    "eicher": "EICHERMOT.NS", "eicher motors": "EICHERMOT.NS", "royal enfield": "EICHERMOT.NS",
    "hero motocorp": "HEROMOTOCO.NS", "hero": "HEROMOTOCO.NS",
    "hindalco": "HINDALCO.NS",
    "jswsteel": "JSWSTEEL.NS", "jsw steel": "JSWSTEEL.NS",
    "m&m": "M&M.NS", "mahindra": "M&M.NS", "mahindra and mahindra": "M&M.NS",
    "tech mahindra": "TECHM.NS", "techm": "TECHM.NS",
    "upl": "UPL.NS",
    "vedanta": "VEDL.NS", "vedl": "VEDL.NS",
    "indusind": "INDUSINDBK.NS", "indusind bank": "INDUSINDBK.NS",
    "axis bank": "AXISBANK.NS", "axis": "AXISBANK.NS",
    "adani enterprises": "ADANIENT.NS", "adani": "ADANIENT.NS",
    "adani ports": "ADANIPORTS.NS",
    "adani green": "ADANIGREEN.NS",
    "adani power": "ADANIPOWER.NS",
    "tata power": "TATAPOWER.NS", "tatapower": "TATAPOWER.NS",
    "tata elxsi": "TATAELXSI.NS",
    "tata consumer": "TATACONSUM.NS",
    "zomato": "ETERNAL.NS",
    "paytm": "PAYTM.NS",
    "irctc": "IRCTC.NS",
    "hal": "HAL.NS", "hindustan aeronautics": "HAL.NS",
    "bhel": "BHEL.NS",
    "ioc": "IOC.NS", "indian oil": "IOC.NS",
    "bpcl": "BPCL.NS", "bharat petroleum": "BPCL.NS",
    "hpcl": "HINDPETRO.NS", "hindustan petroleum": "HINDPETRO.NS",
    "pidilite": "PIDILITIND.NS",
    "dabur": "DABUR.NS",
    "godrej": "GODREJCP.NS", "godrej consumer": "GODREJCP.NS",
    "havells": "HAVELLS.NS",
    "dmart": "DMART.NS", "avenue supermarts": "DMART.NS",
    "sbilife": "SBILIFE.NS", "sbi life": "SBILIFE.NS",
    "hdfc life": "HDFCLIFE.NS", "hdfclife": "HDFCLIFE.NS",
    "icici prudential": "ICICIPRULI.NS",
}

_INDEX_TICKERS: dict[str, str] = {
    # India
    "nifty 50": "^NSEI", "nifty50": "^NSEI", "nifty": "^NSEI",
    "sensex": "^BSESN", "bse sensex": "^BSESN", "bse": "^BSESN",
    "bank nifty": "^NSEBANK", "banknifty": "^NSEBANK", "nifty bank": "^NSEBANK",
    "nifty it": "^CNXIT", "nifty pharma": "^CNXPHARMA",
    "nifty next 50": "^NSMIDCP", "nifty midcap": "^NSMIDCP",
    "india vix": "^INDIAVIX", "vix india": "^INDIAVIX",
    # US
    "s&p 500": "^GSPC", "s&p500": "^GSPC", "sp500": "^GSPC", "s&p": "^GSPC",
    "dow jones": "^DJI", "dow": "^DJI", "djia": "^DJI",
    "nasdaq": "^IXIC", "nasdaq composite": "^IXIC",
    "nasdaq 100": "^NDX", "nasdaq100": "^NDX",
    "russell 2000": "^RUT", "russell": "^RUT",
    "vix": "^VIX", "volatility index": "^VIX", "fear index": "^VIX",
    # Europe
    "ftse 100": "^FTSE", "ftse": "^FTSE",
    "dax": "^GDAXI", "dax 40": "^GDAXI",
    "cac 40": "^FCHI", "cac": "^FCHI",
    "euro stoxx": "^STOXX50E",
    # Asia
    "nikkei": "^N225", "nikkei 225": "^N225",
    "hang seng": "^HSI", "hsi": "^HSI",
    "shanghai": "000001.SS", "sse": "000001.SS",
    "kospi": "^KS11",
    "asx 200": "^AXJO", "asx": "^AXJO",
}

_CRYPTO_TICKERS: dict[str, str] = {
    # Top 10 by market cap
    "bitcoin": "BTC-USD", "btc": "BTC-USD",
    "ethereum": "ETH-USD", "eth": "ETH-USD",
    "tether": "USDT-USD", "usdt": "USDT-USD",
    "bnb": "BNB-USD", "binance coin": "BNB-USD", "binance": "BNB-USD",
    "solana": "SOL-USD", "sol": "SOL-USD",
    "xrp": "XRP-USD", "ripple": "XRP-USD",
    "usdc": "USDC-USD", "usd coin": "USDC-USD",
    "cardano": "ADA-USD", "ada": "ADA-USD",
    "dogecoin": "DOGE-USD", "doge": "DOGE-USD",
    "tron": "TRX-USD", "trx": "TRX-USD",
    # Top 11-30
    "avalanche": "AVAX-USD", "avax": "AVAX-USD",
    "shiba inu": "SHIB-USD", "shib": "SHIB-USD",
    "polkadot": "DOT-USD", "dot": "DOT-USD",
    "chainlink": "LINK-USD", "link": "LINK-USD",
    "litecoin": "LTC-USD", "ltc": "LTC-USD",
    "polygon": "MATIC-USD", "matic": "MATIC-USD",
    "uniswap": "UNI7083-USD", "uni": "UNI7083-USD",
    "cosmos": "ATOM-USD", "atom": "ATOM-USD",
    "monero": "XMR-USD", "xmr": "XMR-USD",
    "stellar": "XLM-USD", "xlm": "XLM-USD",
    "near": "NEAR-USD", "near protocol": "NEAR-USD",
    "filecoin": "FIL-USD", "fil": "FIL-USD",
    "aptos": "APT21794-USD", "apt": "APT21794-USD",
    "arbitrum": "ARB-USD", "arb": "ARB-USD",
    "optimism": "OP-USD",
    "aave": "AAVE-USD",
    "maker": "MKR-USD", "mkr": "MKR-USD",
    "algorand": "ALGO-USD", "algo": "ALGO-USD",
    "pepe": "PEPE24478-USD",
    "sui": "SUI20947-USD",
    "sei": "SEI-USD",
    "injective": "INJ-USD", "inj": "INJ-USD",
    "render": "RENDER-USD", "rndr": "RENDER-USD",
    "fetch.ai": "FET-USD", "fet": "FET-USD",
}


# Tickers or ticker prefixes that are common English words or single/double letters.
# We block these from being matched as bare words to avoid false positive matches.
# They can still be matched if explicitly prefixed with '$' (e.g. $COST, $F) or via company names (e.g. Costco, Ford).
_TICKER_BLOCKLIST = {
    # Single letters
    "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
    # Common English words/conjunctions/pronouns/prepositions
    "am", "an", "as", "at", "be", "by", "do", "go", "he", "if", "in", "is", "it", "me", "my", "no", "of", "on", "or", "so", "to", "up", "us", "we",
    "all", "and", "are", "but", "can", "for", "has", "her", "him", "his", "how", "its", "not", "one", "out", "she", "the", "too", "was", "who", "you",
    "cost", "now", "cat", "arm", "link", "near", "run", "key", "play", "save", "good", "well", "plug", "care", "fast", "free", "grow", "hope",
    "hurt", "life", "love", "mind", "next", "pace", "plan", "post", "real", "safe", "step", "talk", "team", "time", "true", "walk", "wave", "work", "year",
    "dot", "op"
}


def extract_tickers(query: str) -> list[str]:
    """
    Extract ticker symbols from a natural-language query.
    Looks for known names, explicit $SYMBOLS, and .NS suffixes.
    """
    q_lower = query.lower()
    tickers: list[str] = []

    # Explicit $TICKER mentions
    explicit = re.findall(r"\$([A-Z]{1,6})", query.upper())
    tickers.extend(explicit)

    # Explicit TICKER.NS mentions
    ns_tickers = re.findall(r"([A-Z]{2,20}\.NS)", query.upper())
    tickers.extend(ns_tickers)

    # Combine all dictionaries
    all_mappings = {**_US_TICKERS, **_INDIA_TICKERS, **_INDEX_TICKERS, **_CRYPTO_TICKERS, **COMMODITY_TICKERS, **FOREX_PAIRS}
    
    # Add reverse lookup for bare tickers (e.g., 'aapl' -> 'AAPL')
    for _, ticker in list(all_mappings.items()):
        ticker_lower = ticker.lower()
        if ticker_lower not in _TICKER_BLOCKLIST:
            all_mappings[ticker_lower] = ticker
            
        # Also allow prefixes like 'btc' for 'BTC-USD'
        if "-" in ticker:
            prefix = ticker.split("-")[0].lower()
            if prefix not in _TICKER_BLOCKLIST:
                all_mappings[prefix] = ticker
        if "=" in ticker:
            prefix = ticker.split("=")[0].lower()
            if prefix not in _TICKER_BLOCKLIST:
                all_mappings[prefix] = ticker
        if ".NS" in ticker:
            prefix = ticker.split(".")[0].lower()
            if prefix not in _TICKER_BLOCKLIST:
                all_mappings[prefix] = ticker

    # Match blocklisted tickers only if they appear in EXACT UPPERCASE in the original query
    for _, ticker in list(all_mappings.items()):
        ticker_upper = ticker.upper()
        # Clean up suffixes
        clean_ticker = ticker_upper
        if "-" in clean_ticker:
            clean_ticker = clean_ticker.split("-")[0]
        elif "=" in clean_ticker:
            clean_ticker = clean_ticker.split("=")[0]
        elif ".NS" in clean_ticker:
            clean_ticker = clean_ticker.split(".")[0]
        
        if clean_ticker.lower() in _TICKER_BLOCKLIST:
            pattern = r"\b" + re.escape(clean_ticker) + r"\b"
            if clean_ticker.upper() == "C":
                pattern = r"\bC\b(?!\+\+|#)"
            if re.search(pattern, query):
                tickers.append(ticker)

    # Search using word boundaries to avoid partial matches
    for name, ticker in all_mappings.items():
        # Special case: skip 'target' matching 'TGT' if user says 'target price'
        if name == "target" and "target price" in q_lower:
            continue
        pattern = r"\b" + re.escape(name) + r"\b"
        if name.lower() == "c":
            pattern = r"\bc\b(?!\+\+|#)"
        if re.search(pattern, q_lower):
            tickers.append(ticker)

    return list(dict.fromkeys(tickers))  # deduplicate, preserve order


def _fetch_ticker_data(symbol: str) -> dict:
    """Fetch live data for a single ticker."""
    try:
        tk = yf.Ticker(symbol)
        
        # Try fast_info first to avoid heavy scraper calls and rate limits
        try:
            fast = dict(tk.fast_info)
            price = fast.get("lastPrice") or fast.get("regularMarketPrice")
            prev_close = fast.get("previousClose") or fast.get("regularMarketPreviousClose")
            
            result: dict = {
                "symbol": symbol,
                "name": symbol,  # fallback
                "price": round(price, 4) if price else None,
                "previous_close": round(prev_close, 4) if prev_close else None,
                "open": round(fast.get("open"), 4) if fast.get("open") else None,
                "day_high": round(fast.get("dayHigh"), 4) if fast.get("dayHigh") else None,
                "day_low": round(fast.get("dayLow"), 4) if fast.get("dayLow") else None,
                "volume": fast.get("lastVolume") or fast.get("volume"),
                "market_cap": fast.get("marketCap"),
                "currency": fast.get("currency", "INR" if ".NS" in symbol or symbol.startswith("^N") else "USD"),
            }
        except Exception:
            # Fallback to legacy info if fast_info fails
            info = tk.info or {}
            price = (
                info.get("currentPrice")
                or info.get("regularMarketPrice")
                or info.get("regularMarketPreviousClose")
            )
            result = {
                "symbol": symbol,
                "name": info.get("shortName") or info.get("longName", symbol),
                "price": price,
                "previous_close": info.get("previousClose") or info.get("regularMarketPreviousClose"),
                "open": info.get("open") or info.get("regularMarketOpen"),
                "day_high": info.get("dayHigh") or info.get("regularMarketDayHigh"),
                "day_low": info.get("dayLow") or info.get("regularMarketDayLow"),
                "volume": info.get("volume") or info.get("regularMarketVolume"),
                "market_cap": info.get("marketCap"),
                "currency": info.get("currency", "INR" if ".NS" in symbol or symbol.startswith("^N") else "USD"),
            }

        # Fallback: use history if price is still empty
        if not result["price"]:
            try:
                hist = tk.history(period="1d")
                if not hist.empty:
                    result["price"] = round(float(hist["Close"].iloc[-1]), 2)
            except Exception:
                pass

        # Compute change
        if result["price"] and result["previous_close"]:
            change = result["price"] - result["previous_close"]
            pct = (change / result["previous_close"]) * 100
            result["change"] = round(change, 2)
            result["change_percent"] = round(pct, 2)

        return result
    except Exception as exc:
        logger.error("yfinance fetch failed for %s: %s", symbol, exc)
        return {"symbol": symbol, "error": str(exc)}


def get_market_data(query: str) -> dict:
    """
    Main entry point.  Extracts tickers and fetches live data.

    Returns
    -------
    dict with keys: tickers, data, summary
    """
    tickers = extract_tickers(query)
    if not tickers:
        return {"tickers": [], "data": {}, "summary": ""}

    data: dict = {}
    for t in tickers:
        data[t] = _fetch_ticker_data(t)

    summary = format_finance_context(data)
    return {"tickers": tickers, "data": data, "summary": summary}


def format_finance_context(data: dict) -> str:
    """Produce a human-readable summary for context fusion."""
    lines: list[str] = []
    for symbol, info in data.items():
        if "error" in info:
            lines.append(f"• {symbol}: data unavailable ({info['error']})")
            continue
        name = info.get("name", symbol)
        price = info.get("price", "N/A")
        currency = info.get("currency", "USD")
        change = info.get("change", "")
        pct = info.get("change_percent", "")
        cap = info.get("market_cap")
        cap_str = f", Market Cap: {_format_large_number(cap, currency)}" if cap else ""
        change_str = f", Change: {change} ({pct}%)" if change != "" else ""
        lines.append(f"• {name} ({symbol}): {currency} {price}{change_str}{cap_str}")
    return "\n".join(lines) if lines else "No data available."


def _format_large_number(n: Optional[int], currency: str = "USD") -> str:
    if n is None:
        return "N/A"
    if currency == "INR":
        if n >= 10_000_000_000_000:
            return f"₹{n / 100_000_000_000:.2f} Lakh Cr"
        if n >= 10_000_000:
            return f"₹{n / 10_000_000:.2f} Cr"
        if n >= 100_000:
            return f"₹{n / 100_000:.2f} Lakh"
        return f"₹{n:,}"
    else:
        if n >= 1_000_000_000_000:
            return f"${n / 1_000_000_000_000:.2f}T"
        if n >= 1_000_000_000:
            return f"${n / 1_000_000_000:.2f}B"
        if n >= 1_000_000:
            return f"${n / 1_000_000:.2f}M"
        return f"${n:,}"

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
