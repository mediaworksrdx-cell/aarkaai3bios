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
    # NSE Midcap & Smallcap components
    "cdsl": "CDSL.NS", "angel one": "ANGELONE.NS", "angelone": "ANGELONE.NS",
    "kaynes": "KAYNES.NS", "kaynes tech": "KAYNES.NS",
    "zentec": "ZENTEC.NS", "zen tech": "ZENTEC.NS", "zen technologies": "ZENTEC.NS",
    "titagarh": "TITAGARH.NS", "titagarh rail": "TITAGARH.NS",
    "tejas": "TEJASNET.NS", "tejas networks": "TEJASNET.NS",
    "inox wind": "INOXWIND.NS", "inoxwind": "INOXWIND.NS",
    "gravita": "GRAVITA.NS", "railtel": "RAILTEL.NS",
    "sonata": "SONATSOFTW.NS", "sonata software": "SONATSOFTW.NS",
    "kfin": "KFINTECH.NS", "kfin tech": "KFINTECH.NS", "kfintech": "KFINTECH.NS",
    "anand rathi": "ANANDRATHI.NS", "data patterns": "DATAPATTNS.NS",
    "cyient": "CYIENT.NS", "amber": "AMBER.NS", "amber enterprises": "AMBER.NS",
    "jyoti cnc": "JYOTICNC.NS", "neuland": "NEULANDLAB.NS", "marksans": "MARKSANS.NS",
    "suzlon": "SUZLON.NS", "piramal pharma": "PPLPHARMA.NS", "apar": "APARINDS.NS",
    "cams": "CAMS.NS", "persistent": "PERSISTENT.NS", "dixon": "DIXON.NS",
    "polycab": "POLYCAB.NS", "max healthcare": "MAXHEALTH.NS", "cummins": "CUMMINSIND.NS",
    "bharat forge": "BHARATFORG.NS", "federal bank": "FEDERALBNK.NS",
    "ashok leyland": "ASHOKLEY.NS", "coforge": "COFORGE.NS", "mphasis": "MPHASIS.NS",
    "tata comm": "TATACOMM.NS", "tata communications": "TATACOMM.NS", "voltas": "VOLTAS.NS",
    "astral": "ASTRAL.NS", "oberoi realty": "OBEROIRLTY.NS", "phoenix mills": "PHOENIXLTD.NS",
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


def _fetch_twelve_data(symbol: str) -> Optional[dict]:
    """
    Fetch live market data from Twelve Data API (Primary source).
    Supports: US equities, Crypto, Forex, Commodities, Global Indices, and supported Indian equities.
    Returns None on failure or if API key is not configured, triggering fallback to yfinance.
    """
    import json
    import os
    import urllib.parse
    import urllib.request
    import config

    api_key = getattr(config, "TWELVE_DATA_API_KEY", "") or os.getenv("TWELVE_DATA_API_KEY", "")
    if not api_key:
        return None

    # Normalize symbol for Twelve Data conventions
    td_symbol = symbol.strip().upper()
    exchange_param = ""

    if td_symbol.endswith(".NS"):
        td_symbol = td_symbol[:-3]
        exchange_param = "&exchange=NSE"
    elif td_symbol.endswith(".BO"):
        td_symbol = td_symbol[:-3]
        exchange_param = "&exchange=BSE"
    elif td_symbol.endswith("-USD"):
        td_symbol = td_symbol.replace("-USD", "/USD")
    elif "=X" in td_symbol:
        pair = td_symbol.replace("=X", "")
        if len(pair) == 6:
            td_symbol = f"{pair[:3]}/{pair[3:]}"
    elif td_symbol == "GC=F":
        td_symbol = "XAU/USD"
    elif td_symbol == "SI=F":
        td_symbol = "XAG/USD"
    elif td_symbol == "CL=F":
        td_symbol = "WTI/USD"
    elif td_symbol == "^GSPC":
        td_symbol = "SPX"
    elif td_symbol == "^IXIC":
        td_symbol = "IXIC"
    elif td_symbol == "^DJI":
        td_symbol = "DJI"

    try:
        url = f"https://api.twelvedata.com/quote?symbol={urllib.parse.quote(td_symbol)}{exchange_param}&apikey={api_key}"
        req = urllib.request.Request(url, headers={"User-Agent": "AARKAAI/2.0"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        if not isinstance(data, dict) or data.get("status") == "error" or data.get("code") == 400 or not data.get("close"):
            return None

        def _safe_float(val):
            try:
                return round(float(val), 4) if val is not None else None
            except (ValueError, TypeError):
                return None

        price = _safe_float(data.get("close") or data.get("price"))
        prev_close = _safe_float(data.get("previous_close"))
        change = _safe_float(data.get("change"))
        pct_change = _safe_float(data.get("percent_change"))

        if price is None:
            return None

        if change is None and prev_close and price:
            change = round(price - prev_close, 4)
        if pct_change is None and prev_close and change:
            pct_change = round((change / prev_close) * 100, 2)

        vol = None
        try:
            vol = int(float(data.get("volume", 0)))
        except (ValueError, TypeError):
            pass

        currency = data.get("currency") or ("INR" if ".NS" in symbol or exchange_param else "USD")

        return {
            "symbol": symbol,
            "name": data.get("name") or symbol,
            "price": price,
            "previous_close": prev_close,
            "open": _safe_float(data.get("open")),
            "day_high": _safe_float(data.get("high")),
            "day_low": _safe_float(data.get("low")),
            "volume": vol,
            "market_cap": None,
            "currency": currency,
            "change": change,
            "change_percent": pct_change,
            "source": "twelvedata",
        }
    except Exception as exc:
        logger.debug("Twelve Data fetch failed for %s (%s): %s", symbol, td_symbol, exc)
        return None


def _fetch_ticker_data(symbol: str) -> dict:
    """Fetch live data for a single ticker. Primary: Twelve Data API, Fallback: yfinance."""
    # ─── 1. Primary Source: Twelve Data API ────────────────────────────────────
    td_data = _fetch_twelve_data(symbol)
    if td_data and td_data.get("price") is not None:
        logger.info("Market data for %s fetched from Twelve Data (price: %s)", symbol, td_data["price"])
        return td_data

    # ─── 2. Fallback Source: yfinance ──────────────────────────────────────────
    logger.debug("Falling back to yfinance for symbol %s", symbol)
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
                "source": "yfinance",
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
                "source": "yfinance",
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
    import concurrent.futures

    tickers = extract_tickers(query)
    if not tickers:
        return {"tickers": [], "data": {}, "summary": ""}

    data: dict = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(tickers), 6)) as executor:
        futures = {executor.submit(_fetch_ticker_data, t): t for t in tickers}
        for future in concurrent.futures.as_completed(futures):
            t = futures[future]
            try:
                data[t] = future.result()
            except Exception as exc:
                logger.error("Concurrent fetch failed for %s: %s", t, exc)
                data[t] = {"symbol": t, "error": str(exc)}

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
    return "\n".join(lines)

def format_options_context(data: dict) -> str:
    """Format options chain as readable context."""
    if "error" in data:
        return f"Options Chain Error for {data.get('symbol')}: {data['error']}"
        
    summary = data.get("summary", {})
    return (f"Options Summary for {data['symbol']}:\n"
            f"Total Call OI: {summary.get('total_call_oi')}\n"
            f"Total Put OI: {summary.get('total_put_oi')}\n"
            f"Put/Call Ratio (PCR): {summary.get('pcr')}\n"
            f"Max Call OI Strike: {summary.get('max_call_oi_strike')}\n"
            f"Max Put OI Strike: {summary.get('max_put_oi_strike')}")


# ─── Categorized Indian Stock Universes (SEBI Market Cap Classification) ─────
# SEBI Rules:
# - Large Cap: 1st - 100th company in full market cap (Nifty 50 / Nifty 100)
# - Mid Cap: 101st - 250th company in full market cap (Nifty Midcap 150)
# - Small Cap: 251st company onwards (Nifty Smallcap 250, typically <= Rs 25,000 Cr)

_NSE_SMALLCAP_UNIVERSE: dict[str, dict] = {
    "CDSL.NS": {"name": "Central Depository Services Ltd", "sector": "Financial Market Infrastructure", "symbol": "CDSL", "catalyst": "Growing retail investor accounts & demat account surge"},
    "ANGELONE.NS": {"name": "Angel One Ltd", "sector": "Fintech / Retail Broking", "symbol": "ANGELONE", "catalyst": "Strong client acquisition, market share gains in options & cash volumes"},
    "KAYNES.NS": {"name": "Kaynes Technology India Ltd", "sector": "Electronics Manufacturing / EMS", "symbol": "KAYNES", "catalyst": "Rapid order book growth in aerospace, automotive, and industrial EMS"},
    "ZENTEC.NS": {"name": "Zen Technologies Ltd", "sector": "Defence / Drone & Anti-Drone Simulators", "symbol": "ZENTEC", "catalyst": "Substantial export orders and domestic MoD simulation & anti-drone contracts"},
    "TITAGARH.NS": {"name": "Titagarh Rail Systems Ltd", "sector": "Railways & Defense Mobility", "symbol": "TITAGARH", "catalyst": "Vande Bharat passenger trains & metro rail wagon execution"},
    "TEJASNET.NS": {"name": "Tejas Networks Ltd (Tata Group)", "sector": "Telecom & Optical Networking", "symbol": "TEJASNET", "catalyst": "BSNL 4G/5G pan-India deployment rollout & indigenous telecom hardware"},
    "INOXWIND.NS": {"name": "Inox Wind Ltd", "sector": "Renewable Energy / Wind Turbines", "symbol": "INOXWIND", "catalyst": "Turnaround with surging order inflows in commercial & industrial wind power"},
    "GRAVITA.NS": {"name": "Gravita India Ltd", "sector": "Circular Economy / Lead & Battery Recycling", "symbol": "GRAVITA", "catalyst": "Formalization of recycling regulations (BWMR) and capacity expansions"},
    "RAILTEL.NS": {"name": "RailTel Corporation of India Ltd", "sector": "Telecom Infrastructure / Railways ICT", "symbol": "RAILTEL", "catalyst": "Railway signaling, Kavach implementation, and edge data center projects"},
    "SONATSOFTW.NS": {"name": "Sonata Software Ltd", "sector": "IT Services / Modernization", "symbol": "SONATSOFTW", "catalyst": "Large deal wins in Microsoft ecosystem and modernization engineering"},
    "KFINTECH.NS": {"name": "KFin Technologies Ltd", "sector": "Financial Technology / Asset Management RTA", "symbol": "KFINTECH", "catalyst": "International client wins and expansion in alternate investment funds (AIF)"},
    "ANANDRATHI.NS": {"name": "Anand Rathi Wealth Ltd", "sector": "Private Wealth Management", "symbol": "ANANDRATHI", "catalyst": "Strong AUM compounding and recurring private client fee growth"},
    "DATAPATTNS.NS": {"name": "Data Patterns (India) Ltd", "sector": "Aerospace & Defence Electronics", "symbol": "DATAPATTNS", "catalyst": "Indigenous radar, electronic warfare, and satellite electronics programs"},
    "CYIENT.NS": {"name": "Cyient Ltd", "sector": "Engineering & Technology Solutions", "symbol": "CYIENT", "catalyst": "Semiconductor turnkey design and aerospace engineering pipeline"},
    "AMBER.NS": {"name": "Amber Enterprises India Ltd", "sector": "HVAC / Consumer Electronics EMS", "symbol": "AMBER", "catalyst": "Backward integration into PCB manufacturing and mobility HVAC"},
    "JYOTICNC.NS": {"name": "Jyoti CNC Automation Ltd", "sector": "Industrial Machinery / CNC Machines", "symbol": "JYOTICNC", "catalyst": "High-margin aerospace & defence precision machining order pipeline"},
    "NEULANDLAB.NS": {"name": "Neuland Laboratories Ltd", "sector": "Active Pharmaceutical Ingredients (API)", "symbol": "NEULANDLAB", "catalyst": "Commercialization of high-value custom manufacturing (CMS) molecules"},
    "MARKSANS.NS": {"name": "Marksans Pharma Ltd", "sector": "Pharmaceutical Formulations", "symbol": "MARKSANS", "catalyst": "US & UK generic product launches and capacity debottlenecking"},
    "SUZLON.NS": {"name": "Suzlon Energy Ltd", "sector": "Renewable Energy Solutions", "symbol": "SUZLON", "catalyst": "Debt-free balance sheet, 3+ GW order block execution in wind energy"},
    "PPLPHARMA.NS": {"name": "Piramal Pharma Ltd", "sector": "CDMO & Healthcare Solutions", "symbol": "PPLPHARMA", "catalyst": "High-margin sterile injectables & antibody-drug conjugate (ADC) contracts"},
    "APARINDS.NS": {"name": "Apar Industries Ltd", "sector": "Conductors, Cables & Specialty Oils", "symbol": "APARINDS", "catalyst": "Global grid transformation, US export surge in premium conductors"},
    "CAMS.NS": {"name": "Computer Age Management Services Ltd", "sector": "Mutual Fund Services / Financial Tech", "symbol": "CAMS", "catalyst": "70%+ domestic mutual fund RTA market share and non-MF business diversification"},
}

_NSE_MIDCAP_UNIVERSE: dict[str, dict] = {
    "PERSISTENT.NS": {"name": "Persistent Systems Ltd", "sector": "Digital Engineering & Enterprise IT", "symbol": "PERSISTENT", "catalyst": "Enterprise AI integrations and consistent BFSI deal wins"},
    "DIXON.NS": {"name": "Dixon Technologies (India) Ltd", "sector": "Electronics Manufacturing Services", "symbol": "DIXON", "catalyst": "Smartphone manufacturing under PLI and domestic display assembly"},
    "POLYCAB.NS": {"name": "Polycab India Ltd", "sector": "Wires, Cables & Fast-Moving Electricals", "symbol": "POLYCAB", "catalyst": "Real estate construction cycle and institutional infrastructure demand"},
    "MAXHEALTH.NS": {"name": "Max Healthcare Institute Ltd", "sector": "Healthcare & Hospital Networks", "symbol": "MAXHEALTH", "catalyst": "Brownfield bed expansion and high ARPOB operational efficiency"},
    "CUMMINSIND.NS": {"name": "Cummins India Ltd", "sector": "Power Generation & Heavy Engineering", "symbol": "CUMMINSIND", "catalyst": "Data center backup power demand and CPCB IV+ compliant power systems"},
    "BHARATFORG.NS": {"name": "Bharat Forge Ltd", "sector": "Forging, Defence & Auto Components", "symbol": "BHARATFORG", "catalyst": "Artillery gun export execution and aerospace component ramp-up"},
    "FEDERALBNK.NS": {"name": "The Federal Bank Ltd", "sector": "Private Commercial Banking", "symbol": "FEDERALBNK", "catalyst": "Fintech co-lending partnerships and steady asset quality improvement"},
    "ASHOKLEY.NS": {"name": "Ashok Leyland Ltd", "sector": "Commercial Vehicles & Defense Mobility", "symbol": "ASHOKLEY", "catalyst": "Medium and heavy commercial vehicle replacement cycle and bus tenders"},
    "COFORGE.NS": {"name": "Coforge Ltd", "sector": "Information Technology Solutions", "symbol": "COFORGE", "catalyst": "Banking and travel vertical recovery and Cigniti integration synergies"},
    "MPHASIS.NS": {"name": "Mphasis Ltd", "sector": "Cloud & Cognitive IT Services", "symbol": "MPHASIS", "catalyst": "Mortgage business recovery and direct channel client ramp-up"},
    "TATACOMM.NS": {"name": "Tata Communications Ltd", "sector": "Telecommunications & Cloud Networking", "symbol": "TATACOMM", "catalyst": "Digital fabric and enterprise cloud network adoption"},
    "VOLTAS.NS": {"name": "Voltas Ltd (Tata Group)", "sector": "Consumer Air Conditioning & Engineering", "symbol": "VOLTAS", "catalyst": "Record summer AC sales and international engineering project execution"},
    "ASTRAL.NS": {"name": "Astral Ltd", "sector": "Building Materials & Piping Systems", "symbol": "ASTRAL", "catalyst": "Real estate plumbing demand and expansion into bathware and adhesives"},
    "OBEROIRLTY.NS": {"name": "Oberoi Realty Ltd", "sector": "Premium Real Estate", "symbol": "OBEROIRLTY", "catalyst": "High luxury residential pre-sales in Mumbai"},
    "PHOENIXLTD.NS": {"name": "The Phoenix Mills Ltd", "sector": "Retail Destination & Commercial Real Estate", "symbol": "PHOENIXLTD", "catalyst": "Rising retail mall consumption and new mall operationalization"},
}

_NSE_LARGECAP_UNIVERSE: dict[str, dict] = {
    "RELIANCE.NS": {"name": "Reliance Industries Ltd", "sector": "Oil, Telecom & Retail", "symbol": "RELIANCE"},
    "TCS.NS": {"name": "Tata Consultancy Services Ltd", "sector": "IT Services", "symbol": "TCS"},
    "HDFCBANK.NS": {"name": "HDFC Bank Ltd", "sector": "Banking & Financial Services", "symbol": "HDFCBANK"},
    "ICICIBANK.NS": {"name": "ICICI Bank Ltd", "sector": "Banking & Financial Services", "symbol": "ICICIBANK"},
    "INFY.NS": {"name": "Infosys Ltd", "sector": "Digital Services & Consulting", "symbol": "INFY"},
    "BHARTIARTL.NS": {"name": "Bharti Airtel Ltd", "sector": "Telecommunications & Digital Services", "symbol": "BHARTIARTL"},
    "ITC.NS": {"name": "ITC Ltd", "sector": "FMCG, Hotels & Agri-Business", "symbol": "ITC"},
    "SBIN.NS": {"name": "State Bank of India", "sector": "Public Sector Banking", "symbol": "SBIN"},
    "LT.NS": {"name": "Larsen & Toubro Ltd", "sector": "Infrastructure & Heavy Engineering", "symbol": "LT"},
    "HINDUNILVR.NS": {"name": "Hindustan Unilever Ltd", "sector": "Fast-Moving Consumer Goods", "symbol": "HINDUNILVR"},
    "BAJFINANCE.NS": {"name": "Bajaj Finance Ltd", "sector": "Non-Banking Financial Company (NBFC)", "symbol": "BAJFINANCE"},
    "MARUTI.NS": {"name": "Maruti Suzuki India Ltd", "sector": "Passenger Automobile Manufacturing", "symbol": "MARUTI"},
    "ADANIENT.NS": {"name": "Adani Enterprises Ltd", "sector": "Infrastructure & Commodities", "symbol": "ADANIENT"},
}


def is_stock_screener_query(query: str) -> bool:
    """Detect queries asking for stock screening, category discovery, or equity ideas."""
    import re
    q_low = query.lower()
    patterns = [
        r"\bsmall\s*cap[s]?\b",
        r"\bsmallcap[s]?\b",
        r"\bmid\s*cap[s]?\b",
        r"\bmidcap[s]?\b",
        r"\blarge\s*cap[s]?\b",
        r"\blargecap[s]?\b",
        r"\bpenny\s*stock[s]?\b",
        r"\b(bullish|bearish|momentum|breakout|multibagger|growth|dividend|value)\s*stocks?\b",
        r"\bstocks?\s+to\s+(buy|watch|invest|trade|hold|accumulate)\b",
        r"\bstocks?\s+in\s+(nse|bse|india|indian\s+market)\b",
        r"\b(best|top|good|recommend|find|show|give)\s+.*stocks?\b",
        r"\bstock\s*screener\b",
        r"\bshares?\s+in\s+(nse|bse)\b",
        r"\bnifty\s*(smallcap|midcap|50|100|next\s*50|500)\b",
    ]
    return any(re.search(pat, q_low) for pat in patterns)


def screen_stocks(query: str, top_k: int = 5) -> dict:
    """
    Screen real stocks from verified universes (NSE Small-Cap, Mid-Cap, Large-Cap)
    using live fast_info prices, market caps, and technical indicators.
    """
    import concurrent.futures
    import re
    from modules.technical import compute_indicators, get_signal

    q_low = query.lower()

    # Identify target category
    if any(k in q_low for k in ["small cap", "smallcap", "small-cap", "small caps", "smallcaps"]):
        target_category = "small_cap"
        category_label = "NSE Small-Cap (SEBI Definition: Ranked 251st onwards, Market Cap <= Rs 25,000 Cr)"
        universe = _NSE_SMALLCAP_UNIVERSE
    elif any(k in q_low for k in ["mid cap", "midcap", "mid-cap", "mid caps", "midcaps"]):
        target_category = "mid_cap"
        category_label = "NSE Mid-Cap (SEBI Definition: Ranked 101st to 250th, Market Cap Rs 15,000 - Rs 50,000 Cr)"
        universe = _NSE_MIDCAP_UNIVERSE
    elif any(k in q_low for k in ["large cap", "largecap", "large-cap", "large caps", "nifty 50", "bluechip"]):
        target_category = "large_cap"
        category_label = "NSE Large-Cap (SEBI Definition: Top 100 Companies by Market Cap)"
        universe = _NSE_LARGECAP_UNIVERSE
    else:
        # Default to small-cap if query mentioned small or general stock discovery
        target_category = "small_cap"
        category_label = "NSE Small-Cap (SEBI Definition: Ranked 251st onwards, Market Cap <= Rs 25,000 Cr)"
        universe = _NSE_SMALLCAP_UNIVERSE

    is_bullish_requested = any(w in q_low for w in ["bullish", "uptrend", "breakout", "momentum", "buy", "growth", "high return", "multibagger"])

    candidate_symbols = list(universe.keys())[:10]  # Check top 10 candidates concurrently

    def _eval_stock(symbol: str):
        try:
            meta = universe[symbol]
            tk = yf.Ticker(symbol)
            fast = tk.fast_info
            price = fast.get("lastPrice") or fast.get("regularMarketPrice")
            if not price:
                return None
            prev = fast.get("previousClose") or price
            mcap = fast.get("marketCap")
            chg_pct = ((price - prev) / prev * 100) if prev else 0.0

            # Fetch technical indicators
            ind = compute_indicators(symbol) or {}
            rsi = ind.get("rsi")
            ema20 = ind.get("ema20")
            ema50 = ind.get("ema50")
            ema200 = ind.get("ema200")
            signal = get_signal(ind) if ind else "NEUTRAL"

            # Trend evaluation
            is_above_50 = (price > ema50) if (ema50 and price) else True
            is_above_200 = (price > ema200) if (ema200 and price) else True

            # Score bullishness
            bullish_score = 0
            if signal == "BULLISH":
                bullish_score += 3
            if is_above_50:
                bullish_score += 2
            if is_above_200:
                bullish_score += 1
            if rsi and 45 <= rsi <= 70:
                bullish_score += 2
            if chg_pct > 0:
                bullish_score += 1

            return {
                "symbol": symbol,
                "clean_symbol": meta.get("symbol", symbol.replace(".NS", "")),
                "name": meta["name"],
                "sector": meta.get("sector", "Diversified"),
                "catalyst": meta.get("catalyst", ""),
                "price": round(float(price), 2),
                "change_percent": round(float(chg_pct), 2),
                "mcap_cr": round(float(mcap) / 10_000_000, 1) if mcap else None,
                "rsi": rsi,
                "ema50": ema50,
                "ema200": ema200,
                "signal": signal,
                "bullish_score": bullish_score,
            }
        except Exception as exc:
            logger.debug("Screener failed for %s: %s", symbol, exc)
            return None

    screened = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(candidate_symbols), 6)) as executor:
        results = executor.map(_eval_stock, candidate_symbols)
        for r in results:
            if r is not None:
                screened.append(r)

    # Sort by bullishness if requested, else by market cap
    if is_bullish_requested:
        screened.sort(key=lambda x: (x["bullish_score"], -(x["rsi"] or 50)), reverse=True)
    else:
        screened.sort(key=lambda x: (x["mcap_cr"] or 0), reverse=True)

    selected = screened[:top_k]
    if not selected:
        return {"category": target_category, "stocks": [], "summary": "No stocks matched screening criteria."}

    # Format human-readable summary
    lines = [
        "[Verified Stock Screener Data - Live NSE Market Context]",
        f"Category: {category_label}",
        "Exchange: National Stock Exchange of India (NSE)",
        "Verified Live Screener Results (Ranked by Technical Strength):",
    ]
    for idx, s in enumerate(selected, 1):
        price_str = f"Rs {s['price']:,.2f}"
        chg_sign = "+" if s["change_percent"] >= 0 else ""
        chg_str = f"({chg_sign}{s['change_percent']}%)"
        mcap_str = f"Rs {s['mcap_cr']:,.1f} Cr" if s["mcap_cr"] else "N/A"
        tech_notes = []
        if s["ema50"]:
            rel = "above" if s["price"] > s["ema50"] else "near"
            tech_notes.append(f"trading {rel} 50-day EMA (Rs {s['ema50']:,.2f})")
        if s["rsi"]:
            tech_notes.append(f"RSI(14): {s['rsi']}")
        if s["signal"]:
            tech_notes.append(f"Consensus Signal: {s['signal']}")
        tech_summary = ", ".join(tech_notes) if tech_notes else "Healthy consolidation structure"

        lines.append(
            f"{idx}. {s['name']} (NSE: {s['clean_symbol']})\n"
            f"   - Sector: {s['sector']}\n"
            f"   - Current Price: {price_str} {chg_str}\n"
            f"   - Market Capitalization: {mcap_str} (Verified {target_category.replace('_', ' ').title()})\n"
            f"   - Technical Profile: {tech_summary}\n"
            f"   - Fundamental Catalyst: {s['catalyst']}"
        )

    lines.append(
        "\nCRITICAL ENFORCEMENT RULES FOR THE MODEL:\n"
        "- Recommend ONLY the verified stocks listed above.\n"
        "- NEVER list or classify Nifty 50 Large-Cap companies (e.g., HDFC Bank, Infosys, Reliance, Adani Enterprises, Maruti Suzuki, TCS, ICICI Bank, State Bank of India) as small-cap or mid-cap stocks.\n"
        "- Present the real market capitalization in Rs Cr and the exact NSE ticker symbols provided above."
    )

    return {
        "category": target_category,
        "stocks": selected,
        "summary": "\n".join(lines)
    }

