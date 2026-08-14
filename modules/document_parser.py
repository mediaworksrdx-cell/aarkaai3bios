import pdfplumber
import re
import os
import logging
from pathlib import Path
from typing import List, Dict, Any

from config import SAFE_WORK_DIR

logger = logging.getLogger(__name__)

def is_safe_path(file_path: str) -> bool:
    """Validate path against SAFE_WORK_DIR."""
    try:
        target_path = Path(file_path).resolve()
        safe_dir = Path(SAFE_WORK_DIR).resolve()
        return safe_dir in target_path.parents or target_path == safe_dir
    except Exception:
        return False

def parse_pdf(file_path: str) -> dict:
    """Full PDF text extraction with page-by-page content.
    Returns {page_count, pages: [{page_num, text, tables}], total_chars}.
    Tables extracted as list of list[list[str]]."""
    if not is_safe_path(file_path):
        raise ValueError("Invalid file path outside safe workspace")
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    pages_data = []
    total_chars = 0
    
    with pdfplumber.open(file_path) as pdf:
        page_count = len(pdf.pages)
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            tables = page.extract_tables() or []
            
            total_chars += len(text)
            pages_data.append({
                "page_num": i + 1,
                "text": text,
                "tables": tables
            })
            
    return {
        "page_count": page_count,
        "pages": pages_data,
        "total_chars": total_chars
    }

def parse_financial_tables(file_path: str) -> list[dict]:
    """Extract tables from PDF that look like financial statements.
    Heuristic: tables with numeric columns, headers like Revenue/Profit/Assets."""
    pdf_data = parse_pdf(file_path)
    financial_tables = []
    
    fin_keywords = {"revenue", "profit", "assets", "liabilities", "equity", "cash flow", "ebitda", "net income", "operating"}
    
    for page in pdf_data["pages"]:
        for table in page["tables"]:
            if not table or not table[0]:
                continue
                
            # Basic heuristics for financial tables
            headers = [str(h).lower() for h in table[0] if h]
            header_str = " ".join(headers)
            
            is_fin_table = any(kw in header_str for kw in fin_keywords)
            
            if is_fin_table:
                # Guess table type
                table_type = "Unknown"
                if any(kw in header_str for kw in ["assets", "liabilities"]):
                    table_type = "Balance Sheet"
                elif any(kw in header_str for kw in ["revenue", "profit", "ebitda", "net income"]):
                    table_type = "Income Statement"
                elif "cash flow" in header_str:
                    table_type = "Cash Flow"
                    
                financial_tables.append({
                    "page": page["page_num"],
                    "headers": table[0],
                    "rows": table[1:],
                    "table_type_guess": table_type
                })
                
    return financial_tables

def extract_key_figures(text: str) -> dict:
    """Regex extraction of key financial figures from text.
    Extracts: revenue, net_profit, eps, total_assets, total_debt, 
    dividend, market_cap, pat (profit after tax), ebitda."""
    
    # Patterns for generic metrics matching patterns like "Revenue of $1.5M", "Revenue: 1,500 Cr"
    metrics_patterns = {
        "revenue": r"(?i)(?:revenue|turnover|sales)\s*(?:of|at|:|-)?\s*(?:(?:rs\.?|inr|\$|€|£)\s*)?([\d,]+\.?\d*)\s*(cr|crore|mn|million|bn|billion|m|b|k)?",
        "net_profit": r"(?i)(?:net\s*profit|net\s*income|pat)\s*(?:of|at|:|-)?\s*(?:(?:rs\.?|inr|\$|€|£)\s*)?([\d,]+\.?\d*)\s*(cr|crore|mn|million|bn|billion|m|b|k)?",
        "eps": r"(?i)(?:eps|earnings\s*per\s*share)\s*(?:of|at|:|-)?\s*(?:(?:rs\.?|inr|\$|€|£)\s*)?([\d,]+\.?\d*)",
        "total_assets": r"(?i)(?:total\s*assets)\s*(?:of|at|:|-)?\s*(?:(?:rs\.?|inr|\$|€|£)\s*)?([\d,]+\.?\d*)\s*(cr|crore|mn|million|bn|billion|m|b|k)?",
        "total_debt": r"(?i)(?:total\s*debt|borrowings)\s*(?:of|at|:|-)?\s*(?:(?:rs\.?|inr|\$|€|£)\s*)?([\d,]+\.?\d*)\s*(cr|crore|mn|million|bn|billion|m|b|k)?",
        "dividend": r"(?i)(?:dividend)\s*(?:of|at|:|-)?\s*(?:(?:rs\.?|inr|\$|€|£)\s*)?([\d,]+\.?\d*)",
        "market_cap": r"(?i)(?:market\s*cap|market\s*capitalization)\s*(?:of|at|:|-)?\s*(?:(?:rs\.?|inr|\$|€|£)\s*)?([\d,]+\.?\d*)\s*(cr|crore|mn|million|bn|billion|m|b|k)?",
        "pat": r"(?i)(?:pat|profit\s*after\s*tax)\s*(?:of|at|:|-)?\s*(?:(?:rs\.?|inr|\$|€|£)\s*)?([\d,]+\.?\d*)\s*(cr|crore|mn|million|bn|billion|m|b|k)?",
        "ebitda": r"(?i)(?:ebitda)\s*(?:of|at|:|-)?\s*(?:(?:rs\.?|inr|\$|€|£)\s*)?([\d,]+\.?\d*)\s*(cr|crore|mn|million|bn|billion|m|b|k)?"
    }
    
    results = {}
    lines = text.split('\n')
    
    for metric, pattern in metrics_patterns.items():
        for line in lines:
            match = re.search(pattern, line)
            if match:
                value = match.group(1).replace(',', '')
                try:
                    num_val = float(value)
                except ValueError:
                    continue
                    
                multiplier_str = match.group(2).lower() if len(match.groups()) > 1 and match.group(2) else ""
                
                currency = "Unknown"
                if "rs" in line.lower() or "inr" in line.lower() or "cr" in line.lower() or "crore" in line.lower():
                    currency = "INR"
                elif "$" in line:
                    currency = "USD"
                    
                results[metric] = {
                    "value": num_val,
                    "multiplier": multiplier_str,
                    "currency": currency,
                    "context_line": line.strip()
                }
                break # Just get the first match for simplicity
                
    return results

def summarize_document(file_path: str, max_chars: int = 3000) -> str:
    """Quick document summary — first N chars with structure."""
    pdf_data = parse_pdf(file_path)
    
    all_text = ""
    for page in pdf_data["pages"]:
        all_text += f"\n--- Page {page['page_num']} ---\n"
        all_text += page["text"]
        
        if len(all_text) > max_chars:
            break
            
    summary = f"Document Summary (Pages: {pdf_data['page_count']}, Total Chars: {pdf_data['total_chars']})\n"
    summary += "="*50 + "\n"
    summary += all_text[:max_chars]
    
    if len(all_text) > max_chars:
        summary += "\n\n... [Content Truncated] ..."
        
    return summary
