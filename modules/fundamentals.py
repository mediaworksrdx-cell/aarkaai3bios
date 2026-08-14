import logging
import yfinance as yf
import json
from typing import Dict, Any

logger = logging.getLogger(__name__)

def format_number(num) -> str:
    if num is None:
        return "N/A"
    try:
        n = float(num)
        if abs(n) >= 1e9:
            return f"{n / 1e9:.2f}B"
        elif abs(n) >= 1e6:
            return f"{n / 1e6:.2f}M"
        elif abs(n) >= 1e3:
            return f"{n / 1e3:.2f}K"
        else:
            return f"{n:.2f}"
    except (ValueError, TypeError):
        return str(num)

def get_financial_statements(symbol: str, statement_type: str = "income") -> dict:
    """Fetch income statement, balance sheet, or cash flow.
    statement_type: 'income', 'balance', 'cashflow'
    Returns dict with annual and quarterly data formatted as tables."""
    try:
        ticker = yf.Ticker(symbol)
        if statement_type == "income":
            annual = ticker.income_stmt
            quarterly = ticker.quarterly_income_stmt
        elif statement_type == "balance":
            annual = ticker.balance_sheet
            quarterly = ticker.quarterly_balance_sheet
        elif statement_type == "cashflow":
            annual = ticker.cashflow
            quarterly = ticker.quarterly_cashflow
        else:
            return {"error": f"Invalid statement_type: {statement_type}"}

        annual_dict = annual.to_dict() if annual is not None and not annual.empty else {}
        quarterly_dict = quarterly.to_dict() if quarterly is not None and not quarterly.empty else {}
        
        # Convert timestamp keys to string
        annual_res = {str(k.date()): v for k, v in annual_dict.items()} if annual_dict else {}
        quarterly_res = {str(k.date()): v for k, v in quarterly_dict.items()} if quarterly_dict else {}

        return {
            "annual": annual_res,
            "quarterly": quarterly_res
        }
    except Exception as e:
        logger.error(f"Error in get_financial_statements for {symbol}: {e}")
        return {"annual": {}, "quarterly": {}}

def get_key_ratios(symbol: str) -> dict:
    """Key financial ratios: PE, PB, PS, EV/EBITDA, dividend yield, ROE, ROA,
    debt_to_equity, current_ratio, EPS, revenue_growth, profit_margin."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not info:
            return {}

        return {
            "PE": info.get("trailingPE"),
            "PB": info.get("priceToBook"),
            "PS": info.get("priceToSalesTrailing12Months"),
            "EV/EBITDA": info.get("enterpriseToEbitda"),
            "dividend_yield": info.get("dividendYield"),
            "ROE": info.get("returnOnEquity"),
            "ROA": info.get("returnOnAssets"),
            "debt_to_equity": info.get("debtToEquity"),
            "current_ratio": info.get("currentRatio"),
            "EPS": info.get("trailingEps"),
            "revenue_growth": info.get("revenueGrowth"),
            "profit_margin": info.get("profitMargins")
        }
    except Exception as e:
        logger.error(f"Error in get_key_ratios for {symbol}: {e}")
        return {}

def get_earnings(symbol: str) -> dict:
    """Earnings history + estimates. Returns quarterly earnings, EPS trend, revenue estimates."""
    try:
        ticker = yf.Ticker(symbol)
        earnings = ticker.earnings_dates
        if earnings is not None and not earnings.empty:
            earnings_dict = {str(k): v for k, v in earnings.head(4).to_dict(orient="index").items()}
        else:
            earnings_dict = {}

        return {
            "quarterly_earnings": earnings_dict,
            "eps_trend": ticker.eps_trend.to_dict() if ticker.eps_trend is not None and not ticker.eps_trend.empty else {},
            "revenue_estimates": ticker.revenue_estimate.to_dict() if ticker.revenue_estimate is not None and not ticker.revenue_estimate.empty else {}
        }
    except Exception as e:
        logger.error(f"Error in get_earnings for {symbol}: {e}")
        return {"quarterly_earnings": {}, "eps_trend": {}, "revenue_estimates": {}}

def get_company_info(symbol: str) -> dict:
    """Company profile: sector, industry, description, employees, website, market_cap, country."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        if not info:
            return {}

        return {
            "sector": info.get("sector", "N/A"),
            "industry": info.get("industry", "N/A"),
            "description": info.get("longBusinessSummary", "N/A"),
            "employees": info.get("fullTimeEmployees", "N/A"),
            "website": info.get("website", "N/A"),
            "market_cap": info.get("marketCap", "N/A"),
            "country": info.get("country", "N/A")
        }
    except Exception as e:
        logger.error(f"Error in get_company_info for {symbol}: {e}")
        return {}

def format_fundamentals_context(data: dict, data_type: str) -> str:
    """Format fundamental data as readable context string."""
    try:
        if not data:
            return f"No {data_type} data available."
        
        lines = [f"--- {data_type.upper()} DATA ---"]
        
        if data_type == "ratios":
            for k, v in data.items():
                lines.append(f"{k}: {format_number(v)}")
        elif data_type == "company_info":
            for k, v in data.items():
                if k == "market_cap":
                    lines.append(f"{k}: {format_number(v)}")
                else:
                    lines.append(f"{k}: {v}")
        else:
            lines.append(json.dumps(data, indent=2, default=str))
            
        return "\n".join(lines)
    except Exception as e:
        logger.error(f"Error in format_fundamentals_context: {e}")
        return f"Error formatting {data_type} data."
