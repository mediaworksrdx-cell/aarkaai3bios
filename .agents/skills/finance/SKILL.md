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
