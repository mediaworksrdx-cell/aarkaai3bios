"""
Fetch live prices for ALL tickers across:
  - Commodities
  - Currency (Forex)
  - Crypto
  - India (NSE)
  - US Stocks
  - Market Indices

Uses yfinance for real-time data in a single highly-optimized batch request.
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import yfinance as yf
import json
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
    "Weyerhaeuser (Timber)": "WY",
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
    "Uniswap": "UNI7083-USD",
    "Cosmos": "ATOM-USD",
    "Monero": "XMR-USD",
    "Stellar": "XLM-USD",
    "NEAR Protocol": "NEAR-USD",
    "Filecoin": "FIL-USD",
    "Aptos": "APT21794-USD",
    "Arbitrum": "ARB-USD",
    "Optimism": "OP-USD",
    "Aave": "AAVE-USD",
    "Maker": "MKR-USD",
    "Algorand": "ALGO-USD",
    "Hedera": "HBAR-USD",
    "Pepe": "PEPE24478-USD",
    "Sui": "SUI20947-USD",
    "Sei": "SEI-USD",
    "Injective": "INJ-USD",
    "Render": "RENDER-USD",
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
    "Tata Motors (PV)": "TMPV.NS",
    "Tata Motors (CV)": "TMCV.NS",
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
    "Eternal (Zomato)": "ETERNAL.NS",
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
    "Block (Square)": "XYZ",
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


def parse_dataframe(df, symbols_map):
    """
    Extract latest price and previous close from downloaded dataframe.
    Extremely robust handling of NaNs due to timezone variations.
    """
    results = {}
    for name, symbol in symbols_map.items():
        try:
            # Extract column series for Close
            if symbol in df['Close'].columns:
                close_series = df['Close'][symbol].dropna()
            else:
                # Handle single column output from yfinance
                close_series = df['Close'].dropna()

            if close_series.empty:
                results[symbol] = {"price": None, "error": "No close data found"}
                continue

            price = round(float(close_series.iloc[-1]), 4)
            prev = round(float(close_series.iloc[-2]), 4) if len(close_series) >= 2 else None
            
            change = None
            pct = None
            if price and prev:
                change = round(price - prev, 4)
                pct = round((change / prev) * 100, 2)

            currency = "USD"
            if ".NS" in symbol or symbol.startswith("^N"):
                currency = "INR"

            results[symbol] = {
                "name": name,
                "symbol": symbol,
                "price": price,
                "change": change,
                "change_pct": pct,
                "currency": currency,
            }
        except Exception as e:
            results[symbol] = {"price": None, "error": str(e)}
            
    return results


def main():
    print(f"\n{'#'*80}")
    print(f"  AARKAAI BATCH MARKET DATA FETCH — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*80}")

    categories = [
        ("[INDICES] MARKET INDICES", INDICES),
        ("[CMDTY] COMMODITIES", COMMODITIES),
        ("[FX] FOREX / CURRENCY", FOREX),
        ("[CRYPTO] CRYPTOCURRENCY", CRYPTO),
        ("[INDIA] INDIA (NSE)", INDIA),
        ("[US] US STOCKS", US),
    ]

    # Combine all symbols for batch request
    all_symbols_map = {}
    for _, tickers in categories:
        all_symbols_map.update(tickers)

    all_symbols = list(all_symbols_map.values())
    total_tickers = len(all_symbols)
    print(f"\n  Batch downloading {total_tickers} tickers from Yahoo Finance...")

    # Download everything at once with 5 days window to ensure weekend gaps are bridged
    try:
        df = yf.download(all_symbols, period="5d", progress=True, group_by="column", threads=True)
    except Exception as exc:
        print(f"❌ Batch download failed: {exc}")
        sys.exit(1)

    print("\n  Parsing data...")
    parsed_results = parse_dataframe(df, all_symbols_map)

    # Reconstruct category structure for save
    output_data = {}
    for cat_name, tickers in categories:
        cat_results = []
        print(f"\n{'='*80}")
        print(f"  {cat_name}")
        print(f"{'='*80}")
        print(f"{'Name':<25} {'Symbol':<18} {'Price':>12} {'Change':>10} {'Chg%':>8} {'Currency':>8}")
        print(f"{'-'*25} {'-'*18} {'-'*12} {'-'*10} {'-'*8} {'-'*8}")

        for name, symbol in tickers.items():
            data = parsed_results.get(symbol, {"price": None})
            price = data.get("price")
            change = data.get("change")
            pct = data.get("change_pct")
            currency = data.get("currency", "USD")

            price_str = f"{price:>12.4f}" if price is not None else "      N/A   "
            change_str = f"{change:>+10.4f}" if change is not None else "      N/A "
            pct_str = f"{pct:>+7.2f}%" if pct is not None else "    N/A "
            arrow = "▲" if change and change > 0 else ("▼" if change and change < 0 else "─")

            print(f"{name:<25} {symbol:<18} {price_str} {change_str} {pct_str} {currency:>8} {arrow}")
            
            cat_results.append({
                "name": name,
                "symbol": symbol,
                "price": price,
                "change": change,
                "change_pct": pct,
                "currency": currency,
            })
        output_data[cat_name] = cat_results

    output_file = "live_prices.json"
    with open(output_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tickers": total_tickers,
            "data": output_data,
        }, f, indent=2, default=str)

    print(f"\n{'='*80}")
    print(f"  ✅ All {total_tickers} tickers fetched in batch. Saved to {output_file}")
    print(f"{'='*80}\n")


if __name__ == "__main__":
    main()
