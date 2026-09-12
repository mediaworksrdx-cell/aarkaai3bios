import pytest
from modules.aarkaa_engine import (
    _find_repetition_pos,
    _clean_repetition_boundary,
    _guard_token_stream,
    _get_temperature,
)
from modules.finance import is_stock_screener_query, screen_stocks



def test_clean_repetition_boundary_dangling_clause():
    text = ("Here are the top jewellery stocks:\n"
            "1. Titan Company Ltd - Leading branded player.\n"
            "2. Kalyan Jewellers Ltd - Fast growing retail footprint.\n\n"
            "It is important to note that the Titan Company Ltd - Leading")
    rep_pos = text.rfind("Titan Company Ltd")
    assert rep_pos > 50

    clean_pos = _clean_repetition_boundary(text, rep_pos)
    cleaned = text[:clean_pos].rstrip()

    assert not cleaned.endswith("It is important to note that the")
    assert cleaned.endswith("retail footprint.")
    assert "Titan Company Ltd - Leading branded player." in cleaned
    assert "Kalyan Jewellers Ltd - Fast growing retail footprint." in cleaned


def test_guard_token_stream_repetition_truncation():
    tokens = [
        "Here are ", "two key ", "jewellery ", "companies:\n\n",
        "1. Titan: ", "Tata group company.\n",
        "2. Kalyan: ", "Pan-India presence.\n\n",
        "It is important to note that the ",
        "1. Titan: ", "Tata group company.\n",
        "2. Kalyan: ", "Pan-India presence.\n",
    ]
    output_tokens = list(_guard_token_stream(iter(tokens)))
    full_output = "".join(output_tokens).rstrip()

    assert not full_output.endswith("It is important to note that the")
    assert full_output.count("1. Titan:") == 1
    assert full_output.count("2. Kalyan:") == 1


def test_is_stock_screener_query_sectors():
    assert is_stock_screener_query("i asked for gems and jewellery stocks")
    assert is_stock_screener_query("gems and jewellery stocks")
    assert is_stock_screener_query("recommend textile and apparel stocks")
    assert is_stock_screener_query("stocks in defence sector")
    assert is_stock_screener_query("best railway stocks to buy")


def test_screen_stocks_jewellery_sector():
    res = screen_stocks("i asked for gems and jewellery stocks", top_k=5)
    assert res.get("category") == "gems_jewellery"
    stocks = res.get("stocks", [])
    assert len(stocks) >= 3
    symbols = [s["symbol"] for s in stocks]
    assert any("TITAN" in sym for sym in symbols)
    assert any("KALYAN" in sym for sym in symbols)
    assert "[Verified Institutional Stock Screener Data" in res.get("summary", "")


def test_screen_stocks_textiles_sector():
    res = screen_stocks("recommend textile and garment stocks", top_k=5)
    assert res.get("category") == "textiles"
    stocks = res.get("stocks", [])
    assert len(stocks) >= 3
    symbols = [s["symbol"] for s in stocks]
    assert any(s in ["TRIDENT.NS", "PAGEIND.NS", "KPRMILL.NS", "RAYMOND.NS", "WELSPUNLIV.NS", "GOKEX.NS"] for s in symbols)



def test_temperature_allocation():
    temp_list = _get_temperature("i asked for gems and jewellery stocks", "finance_screener")
    assert temp_list == 0.45

    temp_rec = _get_temperature("recommend top 5 small cap stocks", "finance")
    assert temp_rec == 0.45

    temp_price = _get_temperature("what is the current price and pe of reliance", "price_check")
    assert temp_price == 0.15


def test_screener_brief_query_token_budget():
    from modules.aarkaa_engine import _build_final_prompt
    query = "Here is the requested table of top 10 bullish banking stocks, along with a brief analysis for each stock:"
    context = "[Aarka AI Institutional Screener — Live Market Analysis]\nUniverse: Banking & Financial"
    prompt, tokens, temp = _build_final_prompt(query, context, intent="finance_screener")
    assert tokens >= 3800, f"Expected tokens >= 3800 for screener query, got {tokens}"


def test_ten_stock_screener_no_repetition_false_positive():
    sample_10_stocks = """
| Rank | Company | Ticker | Price | Score | Signal | Conviction | Key Metric |
| --- | ------ | ----- | ---- | ---- | ------- | ---------- | ----------- |
| **1.** | Punjab National Bank | PNB.NS | ₹116.75 (-0.09%) | 6.43/10 | ACCUMULATE | MEDIUM | Strategy, Valuation, Risk (Positive trailing EPS: 19.22 Mid-range of 52-week range) |
| **2.** | LIC Housing Finance | LICHSGFIN.NS | ₹562.90 (+1.92%) | 6.31/10 | ACCUMULATE | MEDIUM | Strategy, Momentum, Risk (Positive trailing EPS: 106.33 Upper half of 52-week range) |
| **3.** | Bandhan Bank Limited | BANDHANBNK.NS | ₹176.52 (+1.45%) | 6.20/10 | ACCUMULATE | MEDIUM | Strategy, Momentum, Risk (Positive trailing EPS: 8.38 Mid-range of 52-week range) |
| **4.** | Bank of Baroda | BANKBARODA.NS | ₹238.13 (+0.21%) | 6.00/10 | ACCUMULATE | MEDIUM | Valuation, Risk (Positive trailing EPS: 35.20 Near 52-week low) |
| **5.** | HDFC Bank Limited | HDFCBANK.NS | ₹1645.10 (+0.45%) | 5.80/10 | HOLD | MEDIUM | Risk, Institutional, Backtest (Positive trailing EPS: 82.10 Near 52-week high) |
| **6.** | State Bank of India | SBIN.NS | ₹782.30 (-0.15%) | 5.75/10 | HOLD | MEDIUM | Strategy, Momentum, Risk (Positive trailing EPS: 68.40 Upper half of 52-week range) |
| **7.** | ICICI Bank | ICICIBANK.NS | ₹1220.00 (+0.80%) | 5.70/10 | HOLD | MEDIUM | Strategy, Valuation, Risk (Positive trailing EPS: 58.10 Upper half of 52-week range) |
| **8.** | Axis Bank | AXISBANK.NS | ₹1180.50 (+0.30%) | 5.65/10 | HOLD | MEDIUM | Strategy, Valuation, Risk (Positive trailing EPS: 74.20 Mid-range of 52-week range) |
| **9.** | Kotak Mahindra Bank | KOTAKBANK.NS | ₹1750.00 (+0.10%) | 5.50/10 | HOLD | MEDIUM | Strategy, Valuation, Risk (Positive trailing EPS: 65.30 Mid-range of 52-week range) |
| **10.** | Federal Bank | FEDERALBNK.NS | ₹192.40 (+1.10%) | 5.45/10 | HOLD | MEDIUM | Strategy, Valuation, Risk (Positive trailing EPS: 18.50 Mid-range of 52-week range) |
"""
    assert _find_repetition_pos(sample_10_stocks) is None

