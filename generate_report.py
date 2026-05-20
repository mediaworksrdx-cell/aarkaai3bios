import json
from datetime import datetime

def generate_report():
    with open("live_prices.json", "r") as f:
        payload = json.load(f)

    timestamp = payload.get("timestamp", datetime.now().isoformat())
    dt = datetime.fromisoformat(timestamp)
    formatted_time = dt.strftime("%B %d, %Y at %I:%M:%S %p")

    markdown = []
    markdown.append("# 📈 Live Market Intelligence Dashboard")
    markdown.append(f"> **Report Generated:** {formatted_time} | **Total Tickers Tracked:** {payload.get('total_tickers', 0)}")
    markdown.append("\nThis report captures the current live prices for Commodities, Currency pairs, Crypto, Indian stocks, and US stocks from Yahoo Finance.\n")

    for cat_name, items in payload.get("data", {}).items():
        # Clean title
        title = cat_name.replace("[", "").replace("]", "")
        markdown.append(f"## {title}")
        markdown.append(f"*Total Active Assets tracked in this sector:* {len(items)}\n")
        
        markdown.append("| Asset Name | Symbol | Live Price | Change | % Change | Currency |")
        markdown.append("| :--- | :--- | :---: | :---: | :---: | :---: |")

        for item in items:
            name = item.get("name", "N/A")
            symbol = item.get("symbol", "N/A")
            price = item.get("price")
            change = item.get("change")
            pct = item.get("change_pct")
            currency = item.get("currency", "USD")

            if price is None:
                price_str = "*N/A*"
                change_str = "-"
                pct_str = "-"
            else:
                price_str = f"**{price:,.4f}**" if price < 5.0 else f"**{price:,.2f}**"
                if change is not None and change != 0:
                    sign = "+" if change > 0 else ""
                    color = "🟢" if change > 0 else "🔴"
                    change_str = f"{color} {sign}{change:,.4f}" if abs(change) < 0.1 else f"{color} {sign}{change:,.2f}"
                    pct_str = f"{sign}{pct:.2f}%"
                else:
                    change_str = "─ 0.00"
                    pct_str = "0.00%"

            markdown.append(f"| {name} | `{symbol}` | {price_str} | {change_str} | {pct_str} | {currency} |")
        
        markdown.append("\n---\n")

    with open("live_prices_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(markdown))

if __name__ == "__main__":
    generate_report()
