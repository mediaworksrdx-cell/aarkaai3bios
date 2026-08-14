import logging
from typing import Any, Dict
from modules.tools.base import Tool
import modules.financial_calculator

logger = logging.getLogger(__name__)

class FinancialCalculatorTool(Tool):
    """
    Financial calculator tool for returns, ratios, and risk metrics.
    """
    name = "FinancialCalculatorTool"
    description = "Financial calculations: CAGR, returns, SIP, DCF, PE valuation, position sizing, margin. Actions: cagr, returns, sip, lumpsum, dcf, pe_value, ddm, risk_reward, position_size, margin, emi, compound_interest"
    risk_level = "SAFE"
    latency_weight = 0.3
    cost_weight = 0.1
    base_confidence = 0.99
    permissions = ["read"]
    supported_languages = ["*"]
    requires_workspace = False
    supports_streaming = False
    estimated_latency_ms = 50

    def execute(self, params: Dict[str, Any]) -> str:
        action = params.get("action", "default")
        
        try:
            if action == "cagr":
                initial = float(params.get("initial_value", 0))
                final = float(params.get("final_value", 0))
                years = float(params.get("years", 1))
                res = modules.financial_calculator.cagr(initial, final, years)
                return f"CAGR Calculation: {res}"
                
            elif action == "returns":
                initial = float(params.get("initial_value", 0))
                final = float(params.get("final_value", 0))
                res = modules.financial_calculator.calculate_returns(initial, final)
                return f"Returns Calculation: {res}"
                
            elif action == "sip":
                monthly = float(params.get("monthly_investment", 0))
                rate = float(params.get("rate", 0))
                years = float(params.get("years", 0))
                res = modules.financial_calculator.sip(monthly, rate, years)
                return f"SIP Calculation: {res}"
                
            elif action == "lumpsum":
                principal = float(params.get("principal", 0))
                rate = float(params.get("rate", 0))
                years = float(params.get("years", 0))
                res = modules.financial_calculator.lumpsum(principal, rate, years)
                return f"Lumpsum Calculation: {res}"
                
            elif action == "dcf":
                cf = params.get("cash_flows", [])
                discount_rate = float(params.get("discount_rate", 0))
                terminal_value = float(params.get("terminal_value", 0))
                res = modules.financial_calculator.dcf(cf, discount_rate, terminal_value)
                return f"DCF Valuation: {res}"
                
            elif action == "pe_value":
                eps = float(params.get("eps", 0))
                pe = float(params.get("pe_ratio", 0))
                res = modules.financial_calculator.pe_value(eps, pe)
                return f"PE Valuation: {res}"
                
            elif action == "ddm":
                dividend = float(params.get("dividend", 0))
                growth_rate = float(params.get("growth_rate", 0))
                required_return = float(params.get("required_return", 0))
                res = modules.financial_calculator.ddm(dividend, growth_rate, required_return)
                return f"Dividend Discount Model (DDM): {res}"
                
            elif action == "risk_reward":
                entry = float(params.get("entry_price", 0))
                stop_loss = float(params.get("stop_loss", 0))
                target = float(params.get("target_price", 0))
                res = modules.financial_calculator.risk_reward(entry, stop_loss, target)
                return f"Risk/Reward Ratio: {res}"
                
            elif action == "position_size":
                capital = float(params.get("capital", 0))
                risk_pct = float(params.get("risk_percentage", 0))
                entry = float(params.get("entry_price", 0))
                stop_loss = float(params.get("stop_loss", 0))
                res = modules.financial_calculator.position_size(capital, risk_pct, entry, stop_loss)
                return f"Position Size Calculation: {res}"
                
            elif action == "margin":
                trade_value = float(params.get("trade_value", 0))
                margin_req = float(params.get("margin_requirement", 0))
                res = modules.financial_calculator.margin(trade_value, margin_req)
                return f"Margin Requirement: {res}"
                
            elif action == "emi":
                principal = float(params.get("principal", 0))
                rate = float(params.get("rate", 0))
                months = float(params.get("months", 0))
                res = modules.financial_calculator.emi(principal, rate, months)
                return f"EMI Calculation: {res}"
                
            elif action == "compound_interest":
                principal = float(params.get("principal", 0))
                rate = float(params.get("rate", 0))
                times = float(params.get("compounds_per_year", 1))
                years = float(params.get("years", 0))
                res = modules.financial_calculator.compound_interest(principal, rate, times, years)
                return f"Compound Interest Calculation: {res}"
                
            return f"Unknown action: {action}"
        except Exception as e:
            logger.error(f"Error in FinancialCalculatorTool: {str(e)}")
            return f"Error: {e}"
