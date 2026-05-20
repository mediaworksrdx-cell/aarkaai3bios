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
        all_mappings[ticker.lower()] = ticker
        # Also allow prefixes like 'btc' for 'BTC-USD'
        if "-" in ticker:
            all_mappings[ticker.split("-")[0].lower()] = ticker
        if "=" in ticker:
            all_mappings[ticker.split("=")[0].lower()] = ticker
        if ".NS" in ticker:
            all_mappings[ticker.split(".")[0].lower()] = ticker

    # Search using word boundaries to avoid partial matches
    for name, ticker in all_mappings.items():
        if re.search(r"\b" + re.escape(name) + r"\b", q_lower):
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
        cap_str = f", Market Cap: {_format_large_number(cap)}" if cap else ""
        change_str = f", Change: {change} ({pct}%)" if change != "" else ""
        lines.append(f"• {name} ({symbol}): {currency} {price}{change_str}{cap_str}")
    return "\n".join(lines) if lines else "No data available."


def _format_large_number(n: Optional[int]) -> str:
    if n is None:
        return "N/A"
    if n >= 1_000_000_000_000:
        return f"${n / 1_000_000_000_000:.2f}T"
    if n >= 1_000_000_000:
        return f"${n / 1_000_000_000:.2f}B"
    if n >= 1_000_000:
        return f"${n / 1_000_000:.2f}M"
    return f"${n:,}"
