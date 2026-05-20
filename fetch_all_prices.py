"""
Fetch live prices for ALL tickers across:
  - Commodities
  - Currency (Forex)
  - Crypto
  - India (NSE)
  - US Stocks
  - Market Indices

Uses yfinance for real-time data.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import yfinance as yf
import json
import sys
from datetime import datetime

# ─── COMMODITIES ──────────────────────────────────────────────────────────────
COMMODITIES = {
    "Gold": "GC=F",
    "Silver": "SI=F",
    "Platinum": "PL=F",
    "Palladium": "PA=F",
    "Crude Oil (WTI)": "CL=F",
    "Brent Crude": "BZ=F",
    "Natural Gas": "NG=F",
    "Heating Oil": "HO=F",
    "Gasoline": "RB=F",
    "Copper": "HG=F",
    "Aluminium": "ALI=F",
    "Corn": "ZC=F",
    "Wheat": "ZW=F",
    "Soybean": "ZS=F",
    "Rice": "ZR=F",
    "Oats": "ZO=F",
    "Sugar": "SB=F",
    "Coffee": "KC=F",
    "Cocoa": "CC=F",
    "Cotton": "CT=F",
    "Lumber": "LBS=F",
    "Orange Juice": "OJ=F",
    "Live Cattle": "LE=F",
    "Lean Hogs": "HE=F",
    "Feeder Cattle": "GF=F",
}

# ─── FOREX / CURRENCY ────────────────────────────────────────────────────────
FOREX = {
    "EUR/USD": "EURUSD=X",
    "GBP/USD": "GBPUSD=X",
    "USD/JPY": "USDJPY=X",
    "USD/CHF": "USDCHF=X",
    "AUD/USD": "AUDUSD=X",
    "USD/CAD": "USDCAD=X",
    "NZD/USD": "NZDUSD=X",
    "USD/INR": "USDINR=X",
    "EUR/INR": "EURINR=X",
    "GBP/INR": "GBPINR=X",
    "JPY/INR": "JPYINR=X",
    "EUR/GBP": "EURGBP=X",
    "EUR/JPY": "EURJPY=X",
    "GBP/JPY": "GBPJPY=X",
    "EUR/CHF": "EURCHF=X",
    "AUD/JPY": "AUDJPY=X",
    "CAD/JPY": "CADJPY=X",
    "USD/SGD": "USDSGD=X",
    "USD/HKD": "USDHKD=X",
    "USD/CNY": "USDCNY=X",
    "USD/TRY": "USDTRY=X",
    "USD/ZAR": "USDZAR=X",
    "USD/MXN": "USDMXN=X",
    "USD/AED": "USDAED=X",
    "USD/SAR": "USDSAR=X",
    "DXY (Dollar Index)": "DX-Y.NYB",
}

# ─── CRYPTO ───────────────────────────────────────────────────────────────────
CRYPTO = {
    "Bitcoin": "BTC-USD",
    "Ethereum": "ETH-USD",
    "Tether": "USDT-USD",
    "BNB": "BNB-USD",
    "Solana": "SOL-USD",
    "XRP": "XRP-USD",
    "USDC": "USDC-USD",
    "Cardano": "ADA-USD",
    "Dogecoin": "DOGE-USD",
    "TRON": "TRX-USD",
    "Avalanche": "AVAX-USD",
    "Shiba Inu": "SHIB-USD",
    "Polkadot": "DOT-USD",
    "Chainlink": "LINK-USD",
    "Litecoin": "LTC-USD",
    "Polygon (MATIC)": "MATIC-USD",
    "Uniswap": "UNI-USD",
    "Cosmos": "ATOM-USD",
    "Monero": "XMR-USD",
    "Stellar": "XLM-USD",
    "NEAR Protocol": "NEAR-USD",
    "Filecoin": "FIL-USD",
    "Aptos": "APT-USD",
    "Arbitrum": "ARB-USD",
    "Optimism": "OP-USD",
    "Aave": "AAVE-USD",
    "Maker": "MKR-USD",
    "Algorand": "ALGO-USD",
    "Fantom": "FTM-USD",
    "Hedera": "HBAR-USD",
    "Pepe": "PEPE-USD",
    "Sui": "SUI-USD",
    "Sei": "SEI-USD",
    "Injective": "INJ-USD",
    "Render": "RNDR-USD",
    "Fetch.ai": "FET-USD",
}

# ─── INDIA (NSE) ──────────────────────────────────────────────────────────────
INDIA = {
    "Reliance": "RELIANCE.NS",
    "TCS": "TCS.NS",
    "Infosys": "INFY.NS",
    "HDFC Bank": "HDFCBANK.NS",
    "ICICI Bank": "ICICIBANK.NS",
    "SBI": "SBIN.NS",
    "Wipro": "WIPRO.NS",
    "HCL Tech": "HCLTECH.NS",
    "Bharti Airtel": "BHARTIARTL.NS",
    "ITC": "ITC.NS",
    "Kotak Bank": "KOTAKBANK.NS",
    "L&T": "LT.NS",
    "Hindustan Unilever": "HINDUNILVR.NS",
    "Bajaj Finance": "BAJFINANCE.NS",
    "Bajaj Finserv": "BAJAJFINSV.NS",
    "Maruti Suzuki": "MARUTI.NS",
    "Tata Motors": "TATAMOTORS.NS",
    "Tata Steel": "TATASTEEL.NS",
    "Sun Pharma": "SUNPHARMA.NS",
    "Titan": "TITAN.NS",
    "Asian Paints": "ASIANPAINT.NS",
    "UltraTech Cement": "ULTRACEMCO.NS",
    "Power Grid": "POWERGRID.NS",
    "NTPC": "NTPC.NS",
    "ONGC": "ONGC.NS",
    "Coal India": "COALINDIA.NS",
    "Grasim": "GRASIM.NS",
    "Nestle India": "NESTLEIND.NS",
    "Britannia": "BRITANNIA.NS",
    "Divi's Lab": "DIVISLAB.NS",
    "Dr Reddy's": "DRREDDY.NS",
    "Cipla": "CIPLA.NS",
    "Eicher Motors": "EICHERMOT.NS",
    "Hero MotoCorp": "HEROMOTOCO.NS",
    "Hindalco": "HINDALCO.NS",
    "JSW Steel": "JSWSTEEL.NS",
    "M&M": "M&M.NS",
    "Tech Mahindra": "TECHM.NS",
    "UPL": "UPL.NS",
    "Vedanta": "VEDL.NS",
    "IndusInd Bank": "INDUSINDBK.NS",
    "Axis Bank": "AXISBANK.NS",
    "Adani Enterprises": "ADANIENT.NS",
    "Adani Ports": "ADANIPORTS.NS",
    "Adani Green": "ADANIGREEN.NS",
    "Adani Power": "ADANIPOWER.NS",
    "Tata Power": "TATAPOWER.NS",
    "Tata Elxsi": "TATAELXSI.NS",
    "Tata Consumer": "TATACONSUM.NS",
    "Zomato": "ZOMATO.NS",
    "Paytm": "PAYTM.NS",
    "IRCTC": "IRCTC.NS",
    "HAL": "HAL.NS",
    "BHEL": "BHEL.NS",
    "Indian Oil": "IOC.NS",
    "BPCL": "BPCL.NS",
    "HPCL": "HINDPETRO.NS",
    "Pidilite": "PIDILITIND.NS",
    "Dabur": "DABUR.NS",
    "Godrej Consumer": "GODREJCP.NS",
    "Havells": "HAVELLS.NS",
    "DMart": "DMART.NS",
    "SBI Life": "SBILIFE.NS",
    "HDFC Life": "HDFCLIFE.NS",
    "ICICI Prudential": "ICICIPRULI.NS",
}

# ─── US STOCKS ────────────────────────────────────────────────────────────────
US = {
    "Apple": "AAPL",
    "Google": "GOOGL",
    "Microsoft": "MSFT",
    "Amazon": "AMZN",
    "Meta": "META",
    "Tesla": "TSLA",
    "Nvidia": "NVDA",
    "AMD": "AMD",
    "Intel": "INTC",
    "Qualcomm": "QCOM",
    "Broadcom": "AVGO",
    "Texas Instruments": "TXN",
    "Micron": "MU",
    "ARM": "ARM",
    "TSMC": "TSM",
    "Salesforce": "CRM",
    "Adobe": "ADBE",
    "Oracle": "ORCL",
    "ServiceNow": "NOW",
    "Snowflake": "SNOW",
    "Palantir": "PLTR",
    "CrowdStrike": "CRWD",
    "Datadog": "DDOG",
    "Twilio": "TWLO",
    "Shopify": "SHOP",
    "Spotify": "SPOT",
    "Netflix": "NFLX",
    "Disney": "DIS",
    "Snap": "SNAP",
    "Pinterest": "PINS",
    "Uber": "UBER",
    "Airbnb": "ABNB",
    "DoorDash": "DASH",
    "Roblox": "RBLX",
    "JPMorgan": "JPM",
    "Goldman Sachs": "GS",
    "Morgan Stanley": "MS",
    "Bank of America": "BAC",
    "Wells Fargo": "WFC",
    "Citigroup": "C",
    "Visa": "V",
    "Mastercard": "MA",
    "PayPal": "PYPL",
    "American Express": "AXP",
    "Block (Square)": "SQ",
    "Charles Schwab": "SCHW",
    "BlackRock": "BLK",
    "Berkshire Hathaway": "BRK-B",
    "J&J": "JNJ",
    "Pfizer": "PFE",
    "UnitedHealth": "UNH",
    "AbbVie": "ABBV",
    "Merck": "MRK",
    "Eli Lilly": "LLY",
    "Moderna": "MRNA",
    "Amgen": "AMGN",
    "Gilead": "GILD",
    "Novo Nordisk": "NVO",
    "Exxon": "XOM",
    "Chevron": "CVX",
    "Shell": "SHEL",
    "ConocoPhillips": "COP",
    "BP": "BP",
    "Schlumberger": "SLB",
    "Walmart": "WMT",
    "Costco": "COST",
    "Home Depot": "HD",
    "Target": "TGT",
    "Coca-Cola": "KO",
    "PepsiCo": "PEP",
    "Procter & Gamble": "PG",
    "Nike": "NKE",
    "Starbucks": "SBUX",
    "McDonald's": "MCD",
    "Boeing": "BA",
    "Lockheed Martin": "LMT",
    "Caterpillar": "CAT",
    "3M": "MMM",
    "Honeywell": "HON",
    "General Electric": "GE",
    "AT&T": "T",
    "Verizon": "VZ",
    "T-Mobile": "TMUS",
    "Ford": "F",
    "General Motors": "GM",
    "Rivian": "RIVN",
    "Lucid": "LCID",
    "NIO": "NIO",
    "IBM": "IBM",
    "Cisco": "CSCO",
    "HP": "HPQ",
    "Dell": "DELL",
}

# ─── INDICES ──────────────────────────────────────────────────────────────────
INDICES = {
    "Nifty 50": "^NSEI",
    "Sensex": "^BSESN",
    "Bank Nifty": "^NSEBANK",
    "S&P 500": "^GSPC",
    "Dow Jones": "^DJI",
    "NASDAQ": "^IXIC",
    "NASDAQ 100": "^NDX",
    "Russell 2000": "^RUT",
    "VIX": "^VIX",
    "India VIX": "^INDIAVIX",
}


def fetch_price(symbol: str) -> dict:
    """Fetch live price data for a single ticker."""
    try:
        tk = yf.Ticker(symbol)
        info = tk.info or {}

        price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("regularMarketPreviousClose")
        )

        # Fallback to history
        if not price:
            try:
                hist = tk.history(period="1d")
                if not hist.empty:
                    price = round(float(hist["Close"].iloc[-1]), 2)
            except Exception:
                pass

        prev = info.get("previousClose") or info.get("regularMarketPreviousClose")
        change = None
        pct = None
        if price and prev:
            change = round(price - prev, 4)
            pct = round((change / prev) * 100, 2)

        return {
            "price": price,
            "prev_close": prev,
            "change": change,
            "change_pct": pct,
            "currency": info.get("currency", "USD"),
            "name": info.get("shortName") or info.get("longName", symbol),
        }
    except Exception as e:
        return {"price": None, "error": str(e)}


def fetch_category(cat_name: str, tickers: dict) -> list:
    """Fetch all tickers in a category and return results."""
    symbols = list(tickers.values())
    names = list(tickers.keys())
    results = []

    print(f"\n{'='*80}")
    print(f"  {cat_name} ({len(symbols)} tickers)")
    print(f"{'='*80}")
    print(f"{'Name':<25} {'Symbol':<18} {'Price':>12} {'Change':>10} {'Chg%':>8} {'Currency':>8}")
    print(f"{'-'*25} {'-'*18} {'-'*12} {'-'*10} {'-'*8} {'-'*8}")

    # Batch download for speed
    try:
        batch = yf.download(symbols, period="1d", group_by="ticker", progress=False, threads=True)
    except Exception:
        batch = None

    for name, symbol in zip(names, symbols):
        data = fetch_price(symbol)
        price = data.get("price")
        change = data.get("change")
        pct = data.get("change_pct")
        currency = data.get("currency", "USD")

        price_str = f"{price:>12.4f}" if price is not None else "      N/A   "
        change_str = f"{change:>+10.4f}" if change is not None else "      N/A "
        pct_str = f"{pct:>+7.2f}%" if pct is not None else "    N/A "

        arrow = ""
        if change is not None:
            arrow = "▲" if change > 0 else ("▼" if change < 0 else "─")

        print(f"{name:<25} {symbol:<18} {price_str} {change_str} {pct_str} {currency:>8} {arrow}")

        results.append({
            "name": name,
            "symbol": symbol,
            "price": price,
            "change": change,
            "change_pct": pct,
            "currency": currency,
        })

    return results


def main():
    print(f"\n{'#'*80}")
    print(f"  AARKAAI LIVE MARKET DATA — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}")

    all_data = {}

    categories = [
        ("[INDICES] MARKET INDICES", INDICES),
        ("[CMDTY] COMMODITIES", COMMODITIES),
        ("[FX] FOREX / CURRENCY", FOREX),
        ("[CRYPTO] CRYPTOCURRENCY", CRYPTO),
        ("[INDIA] INDIA (NSE)", INDIA),
        ("[US] US STOCKS", US),
    ]

    total_tickers = sum(len(v) for _, v in categories)
    print(f"\n  Total tickers to fetch: {total_tickers}")

    for cat_name, tickers in categories:
        results = fetch_category(cat_name, tickers)
        all_data[cat_name] = results

    # Save to JSON
    output_file = "live_prices.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tickers": total_tickers,
            "data": all_data,
        }, f, indent=2, default=str)

    print(f"\n{'='*80}")
    print(f"  ✅ All {total_tickers} tickers fetched. Data saved to {output_file}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
