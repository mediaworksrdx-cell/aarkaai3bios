---
name: finance
description: Quantitative finance and market strategy standards. Use when designing trading algorithms, constructing portfolios, or analyzing market risk.
---

# Quantitative Finance & Trading Standards

When analyzing financial models, trading strategies, or portfolio constructions, adhere to these professional standards:

## 1. Domain Separation
* **Strict Boundary:** Never mix forecasting models with trading execution strategies. Keep alpha generation, execution logic, and risk management as separate, modular layers.

## 2. Key Analytical Requirements
For every financial strategy, you must address:
* **Feature Engineering:** Signal definition, data frequency, and data cleaning.
* **Validation & Testing:** Walk-forward testing, cross-validation, and avoiding lookahead bias or overfitting.
* **Market Regimes:** Strategy performance across different market regimes (e.g., high volatility, trending, mean-reverting).
* **Evaluation Metrics:** Sharpe ratio, Sortino ratio, maximum drawdown, information ratio, and win/loss statistics.
* **Risk & Limitations:** Leverage limits, margin requirements, liquidity constraints, transaction costs, and slippage.
* **Assumptions:** Explicitly list all assumptions regarding market liquidity, borrowing costs, and execution speed.

## 3. Available Tools & Integration
The finance domain has the following tools available for grounded, data-driven responses:

| Tool | Purpose | Key Actions |
|------|---------|-------------|
| `MarketDataTool` | Live prices, OHLCV, options chain | `price`, `ohlcv`, `options_chain`, `oi`, `iv`, `pcr` |
| `FinancialCalculatorTool` | Calculations & valuations | `cagr`, `returns`, `sip`, `lumpsum`, `dcf`, `pe_value`, `ddm`, `risk_reward`, `position_size`, `margin`, `emi`, `compound_interest` |
| `FinancialDataTool` | Fundamental data | `financials`, `ratios`, `earnings`, `company_info` |
| `FinancialNewsTool` | Market & company news | `market_news`, `company_news`, `regulatory_updates` |
| `TechnicalAnalysisTool` | Technical indicators & signals | `indicators`, `signal`, `patterns`, `extended` |
| `FnOAnalyticsTool` | Derivatives analytics | `greeks`, `max_pain`, `pcr`, `iv_analysis`, `oi_analysis` |
| `PortfolioTool` | Portfolio management | `holdings`, `add`, `remove`, `summary`, `risk`, `watchlist_add`, `watchlist_remove`, `watchlist_view` |
| `FinanceCodeTool` | Safe Python execution | `execute` (AST-validated sandbox) |
| `MarketDateTimeTool` | Market sessions & holidays | `market_status`, `next_expiry`, `trading_days`, `time_to_expiry` |

## 4. Mandatory Disclaimers
* Every response involving stock recommendations, trading strategies, or portfolio advice **must** include: _"This is for educational/informational purposes only. Not SEBI-registered investment advice."_
* Options-related responses must additionally state: _"Options trading involves substantial risk of loss. Past performance does not guarantee future results."_

## 5. Data Sourcing Standards
* Always cite data source (yfinance, NSE, BSE) and approximate timestamp.
* Never present stale cached data as live without disclosure.
* For Indian markets, use INR formatting (Lakh, Cr) and NSE ticker symbols.
* For US markets, use USD formatting (M, B, T) and standard ticker symbols.
