import os
import sys
import base64
from io import BytesIO
from datetime import date

# Try imports
try:
    import pandas as pd
    import yfinance as yf
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    from weasyprint import HTML
    print("Imports succeeded!")
except Exception as e:
    print("Import failed:", e)
    sys.exit(1)

def calculate_indicators(df):
    # RSI
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    return df

try:
    print("Fetching AAPL data...")
    ticker = yf.Ticker("AAPL")
    df = ticker.history(period="1y")
    df = calculate_indicators(df)
    
    # Generate Charts
    print("Generating MACD Chart...")
    plt.figure(figsize=(10, 4))
    plt.plot(df.index[-100:], df['MACD'].tail(100), label='MACD', color='blue')
    plt.plot(df.index[-100:], df['Signal'].tail(100), label='Signal', color='red')
    plt.title("AAPL MACD (Last 100 Days)")
    plt.legend()
    plt.tight_layout()
    macd_buf = BytesIO()
    plt.savefig(macd_buf, format='png')
    macd_buf.seek(0)
    macd_b64 = base64.b64encode(macd_buf.read()).decode('utf-8')
    plt.close()

    print("Generating RSI Chart...")
    plt.figure(figsize=(10, 4))
    plt.plot(df.index[-100:], df['RSI'].tail(100), label='RSI', color='purple')
    plt.axhline(70, linestyle='--', color='red', alpha=0.5)
    plt.axhline(30, linestyle='--', color='green', alpha=0.5)
    plt.title("AAPL RSI (Last 100 Days)")
    plt.legend()
    plt.tight_layout()
    rsi_buf = BytesIO()
    plt.savefig(rsi_buf, format='png')
    rsi_buf.seek(0)
    rsi_b64 = base64.b64encode(rsi_buf.read()).decode('utf-8')
    plt.close()

    print("Generating Price Chart...")
    plt.figure(figsize=(10, 4))
    plt.plot(df.index[-100:], df['Close'].tail(100), label='Close Price', color='green')
    plt.title("AAPL Close Price (Last 100 Days)")
    plt.legend()
    plt.tight_layout()
    price_buf = BytesIO()
    plt.savefig(price_buf, format='png')
    price_buf.seek(0)
    price_b64 = base64.b64encode(price_buf.read()).decode('utf-8')
    plt.close()

    # Create HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A4;
                margin: 20mm;
            }}
            body {{
                font-family: 'Helvetica Neue', Arial, sans-serif;
                color: #333333;
                line-height: 1.6;
            }}
            .page {{
                page-break-after: always;
            }}
            .page:last-child {{
                page-break-after: avoid;
            }}
            h1 {{
                color: #1e3a8a;
                font-size: 32px;
                border-bottom: 2px solid #1e3a8a;
                padding-bottom: 10px;
            }}
            h2 {{
                color: #1e3a8a;
                font-size: 22px;
                margin-top: 30px;
            }}
            .chart-img {{
                width: 100%;
                max-width: 650px;
                margin: 20px 0;
                border: 1px solid #ddd;
                border-radius: 4px;
            }}
            .stats-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            .stats-table th, .stats-table td {{
                border: 1px solid #dddddd;
                text-align: left;
                padding: 8px;
            }}
            .stats-table th {{
                background-color: #f2f2f2;
                color: #1e3a8a;
            }}
        </style>
    </head>
    <body>
        <div class="page" style="text-align: center; padding-top: 50px;">
            <h1 style="border: none; font-size: 38px; margin-top: 100px;">Apple Inc. (AAPL)</h1>
            <h2 style="font-size: 26px; color: #555;">Deep Technical Analysis Report</h2>
            <p style="margin-top: 50px; font-size: 16px;">Generated automatically on {date.today().strftime('%B %d, %Y')}</p>
            <div style="margin-top: 150px; font-size: 14px; color: #777;">
                CONFIDENTIAL — FOR INTERNAL USE ONLY
            </div>
        </div>

        <div class="page">
            <h2>1. Market Price Analysis</h2>
            <p>
                The chart below shows the daily closing price of Apple Inc. (AAPL) over the last 100 trading days. 
                Apple has shown strong performance driven by institutional demand, product announcements, and solid quarterly financials.
            </p>
            <img class="chart-img" src="data:image/png;base64,{price_b64}" />
            
            <h3>Key Stats (1-Year Period)</h3>
            <table class="stats-table">
                <tr>
                    <th>Metric</th>
                    <th>Value</th>
                </tr>
                <tr>
                    <td>Latest Close Price</td>
                    <td>${df['Close'].iloc[-1]:.2f}</td>
                </tr>
                <tr>
                    <td>52-Week High</td>
                    <td>${df['High'].max():.2f}</td>
                </tr>
                <tr>
                    <td>52-Week Low</td>
                    <td>${df['Low'].min():.2f}</td>
                </tr>
                <tr>
                    <td>Average Daily Volume</td>
                    <td>{df['Volume'].mean():,.0f} shares</td>
                </tr>
            </table>
        </div>

        <div class="page">
            <h2>2. Moving Average Convergence Divergence (MACD)</h2>
            <p>
                The MACD is a trend-following momentum indicator that shows the relationship between two moving averages of a security's price.
                A crossover of the MACD line above the Signal line indicates bullish momentum, whereas a crossover below indicates bearish momentum.
            </p>
            <img class="chart-img" src="data:image/png;base64,{macd_b64}" />
            <p>
                Current MACD: <strong>{df['MACD'].iloc[-1]:.4f}</strong><br/>
                Current Signal Line: <strong>{df['Signal'].iloc[-1]:.4f}</strong><br/>
                Status: <strong>{"Bullish Momentum (Above Signal)" if df['MACD'].iloc[-1] > df['Signal'].iloc[-1] else "Bearish Momentum (Below Signal)"}</strong>
            </p>
        </div>

        <div class="page">
            <h2>3. Relative Strength Index (RSI)</h2>
            <p>
                RSI is a momentum oscillator that measures the speed and change of price movements between 0 and 100.
                An RSI above 70 indicates a stock may be overbought, while an RSI below 30 indicates it may be oversold.
            </p>
            <img class="chart-img" src="data:image/png;base64,{rsi_b64}" />
            <p>
                Current RSI (14-Day): <strong>{df['RSI'].iloc[-1]:.2f}</strong><br/>
                Condition: <strong>{"Overbought (>70)" if df['RSI'].iloc[-1] > 70 else "Oversold (<30)" if df['RSI'].iloc[-1] < 30 else "Neutral"}</strong>
            </p>
        </div>
    </body>
    </html>
    """
    
    # Save PDF
    pdf_path = "/home/ubuntu/aarkaai3b/workspace/aapl_analysis.pdf"
    print("Writing PDF to", pdf_path)
    HTML(string=html_content).write_pdf(pdf_path)
    print("PDF generation completed successfully!")
    
except Exception as e:
    print("Error during processing:", e)
    sys.exit(1)
