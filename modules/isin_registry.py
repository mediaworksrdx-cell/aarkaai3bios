"""
AARKAAI — Official Security Master & ISIN Registry.

Provides authoritative ISIN (International Securities Identification Number) mappings
and regulatory provenance for Indian equities on NSE / BSE and global markets.
"""
from __future__ import annotations

import re
from typing import Dict, Optional, Tuple

# Official ISIN mappings for Indian liquid large/mid caps and key universe equities
_ISIN_MAP: Dict[str, Dict[str, str]] = {
    "RELIANCE": {
        "symbol": "RELIANCE",
        "ns_symbol": "RELIANCE.NS",
        "name": "Reliance Industries Limited",
        "isin": "INE002A01018",
        "sector": "Power & Energy / Oil & Gas",
        "exchange": "NSE",
    },
    "SUNPHARMA": {
        "symbol": "SUNPHARMA",
        "ns_symbol": "SUNPHARMA.NS",
        "name": "Sun Pharmaceutical Industries Limited",
        "isin": "INE044A01036",
        "sector": "Pharma & Healthcare",
        "exchange": "NSE",
    },
    "TATAMOTORS": {
        "symbol": "TATAMOTORS",
        "ns_symbol": "TATAMOTORS.NS",
        "name": "Tata Motors Limited",
        "isin": "INE155A01022",
        "sector": "Auto & Ancillaries",
        "exchange": "NSE",
    },
    "TCS": {
        "symbol": "TCS",
        "ns_symbol": "TCS.NS",
        "name": "Tata Consultancy Services Limited",
        "isin": "INE467B01029",
        "sector": "IT & Software",
        "exchange": "NSE",
    },
    "INFY": {
        "symbol": "INFY",
        "ns_symbol": "INFY.NS",
        "name": "Infosys Limited",
        "isin": "INE009A01021",
        "sector": "IT & Software",
        "exchange": "NSE",
    },
    "HDFCBANK": {
        "symbol": "HDFCBANK",
        "ns_symbol": "HDFCBANK.NS",
        "name": "HDFC Bank Limited",
        "isin": "INE040A01034",
        "sector": "Banking & Financial Services",
        "exchange": "NSE",
    },
    "ICICIBANK": {
        "symbol": "ICICIBANK",
        "ns_symbol": "ICICIBANK.NS",
        "name": "ICICI Bank Limited",
        "isin": "INE090A01021",
        "sector": "Banking & Financial Services",
        "exchange": "NSE",
    },
    "SBIN": {
        "symbol": "SBIN",
        "ns_symbol": "SBIN.NS",
        "name": "State Bank of India",
        "isin": "INE062A01020",
        "sector": "Banking & Financial Services",
        "exchange": "NSE",
    },
    "BHARTIARTL": {
        "symbol": "BHARTIARTL",
        "ns_symbol": "BHARTIARTL.NS",
        "name": "Bharti Airtel Limited",
        "isin": "INE397D01024",
        "sector": "Telecommunications",
        "exchange": "NSE",
    },
    "ITC": {
        "symbol": "ITC",
        "ns_symbol": "ITC.NS",
        "name": "ITC Limited",
        "isin": "INE154A01025",
        "sector": "FMCG & Consumer Goods",
        "exchange": "NSE",
    },
    "LT": {
        "symbol": "LT",
        "ns_symbol": "LT.NS",
        "name": "Larsen & Toubro Limited",
        "isin": "INE018A01030",
        "sector": "Infrastructure & Capital Goods",
        "exchange": "NSE",
    },
    "BAJFINANCE": {
        "symbol": "BAJFINANCE",
        "ns_symbol": "BAJFINANCE.NS",
        "name": "Bajaj Finance Limited",
        "isin": "INE296A01024",
        "sector": "Banking & Financial Services",
        "exchange": "NSE",
    },
    "KOTAKBANK": {
        "symbol": "KOTAKBANK",
        "ns_symbol": "KOTAKBANK.NS",
        "name": "Kotak Mahindra Bank Limited",
        "isin": "INE237A01028",
        "sector": "Banking & Financial Services",
        "exchange": "NSE",
    },
    "MARUTI": {
        "symbol": "MARUTI",
        "ns_symbol": "MARUTI.NS",
        "name": "Maruti Suzuki India Limited",
        "isin": "INE585B01010",
        "sector": "Auto & Ancillaries",
        "exchange": "NSE",
    },
    "AXISBANK": {
        "symbol": "AXISBANK",
        "ns_symbol": "AXISBANK.NS",
        "name": "Axis Bank Limited",
        "isin": "INE238A01034",
        "sector": "Banking & Financial Services",
        "exchange": "NSE",
    },
    "NTPC": {
        "symbol": "NTPC",
        "ns_symbol": "NTPC.NS",
        "name": "NTPC Limited",
        "isin": "INE733E01010",
        "sector": "Power & Energy",
        "exchange": "NSE",
    },
    "POWERGRID": {
        "symbol": "POWERGRID",
        "ns_symbol": "POWERGRID.NS",
        "name": "Power Grid Corporation of India",
        "isin": "INE752E01010",
        "sector": "Power & Energy",
        "exchange": "NSE",
    },
    "TITAN": {
        "symbol": "TITAN",
        "ns_symbol": "TITAN.NS",
        "name": "Titan Company Limited",
        "isin": "INE280A01028",
        "sector": "Gems & Jewellery",
        "exchange": "NSE",
    },
    "ADANIENT": {
        "symbol": "ADANIENT",
        "ns_symbol": "ADANIENT.NS",
        "name": "Adani Enterprises Limited",
        "isin": "INE423A01024",
        "sector": "Infrastructure & Conglomerates",
        "exchange": "NSE",
    },
    "ADANIPORTS": {
        "symbol": "ADANIPORTS",
        "ns_symbol": "ADANIPORTS.NS",
        "name": "Adani Ports and SEZ Limited",
        "isin": "INE742F01042",
        "sector": "Infrastructure & Logistics",
        "exchange": "NSE",
    },
    "ULTRACEMCO": {
        "symbol": "ULTRACEMCO",
        "ns_symbol": "ULTRACEMCO.NS",
        "name": "UltraTech Cement Limited",
        "isin": "INE481G01011",
        "sector": "Building Materials",
        "exchange": "NSE",
    },
    "CIPLA": {
        "symbol": "CIPLA",
        "ns_symbol": "CIPLA.NS",
        "name": "Cipla Limited",
        "isin": "INE059A01026",
        "sector": "Pharma & Healthcare",
        "exchange": "NSE",
    },
    "DRREDDY": {
        "symbol": "DRREDDY",
        "ns_symbol": "DRREDDY.NS",
        "name": "Dr. Reddy's Laboratories Limited",
        "isin": "INE089A01023",
        "sector": "Pharma & Healthcare",
        "exchange": "NSE",
    },
    "WIPRO": {
        "symbol": "WIPRO",
        "ns_symbol": "WIPRO.NS",
        "name": "Wipro Limited",
        "isin": "INE075A01022",
        "sector": "IT & Software",
        "exchange": "NSE",
    },
    "HCLTECH": {
        "symbol": "HCLTECH",
        "ns_symbol": "HCLTECH.NS",
        "name": "HCL Technologies Limited",
        "isin": "INE860A01027",
        "sector": "IT & Software",
        "exchange": "NSE",
    },
}

# Aliases and common search phrases to root ticker keys
_ALIAS_MAP: Dict[str, str] = {
    "sun pharma": "SUNPHARMA",
    "sun pharmaceutical": "SUNPHARMA",
    "sun pharmaceutical industries": "SUNPHARMA",
    "reliance": "RELIANCE",
    "reliance industries": "RELIANCE",
    "ril": "RELIANCE",
    "tata motors": "TATAMOTORS",
    "tcs": "TCS",
    "tata consultancy": "TCS",
    "infosys": "INFY",
    "hdfc bank": "HDFCBANK",
    "icici bank": "ICICIBANK",
    "state bank of india": "SBIN",
    "sbi": "SBIN",
    "bharti airtel": "BHARTIARTL",
    "airtel": "BHARTIARTL",
    "itc": "ITC",
    "larsen & toubro": "LT",
    "l&t": "LT",
    "bajaj finance": "BAJFINANCE",
    "maruti": "MARUTI",
    "maruti suzuki": "MARUTI",
    "kotak bank": "KOTAKBANK",
    "kotak mahindra": "KOTAKBANK",
    "axis bank": "AXISBANK",
    "ntpc": "NTPC",
    "power grid": "POWERGRID",
    "titan": "TITAN",
    "titan company": "TITAN",
    "adani ent": "ADANIENT",
    "adani ports": "ADANIPORTS",
    "ultratech": "ULTRACEMCO",
    "ultratech cement": "ULTRACEMCO",
}


def lookup_isin(key_or_symbol: str) -> Optional[str]:
    """Resolves an ISIN code from a ticker, name, or symbol alias."""
    if not key_or_symbol:
        return None
    raw = key_or_symbol.strip().upper().replace(".NS", "").replace(".BO", "")
    if raw in _ISIN_MAP:
        return _ISIN_MAP[raw]["isin"]

    clean_low = key_or_symbol.strip().lower()
    for alias, root in _ALIAS_MAP.items():
        if alias in clean_low:
            return _ISIN_MAP[root]["isin"]

    return None


def get_security_master(key_or_symbol: str) -> Optional[Dict[str, str]]:
    """Returns the full master entry (symbol, isin, name, exchange) if known."""
    if not key_or_symbol:
        return None
    raw = key_or_symbol.strip().upper().replace(".NS", "").replace(".BO", "")
    if raw in _ISIN_MAP:
        return dict(_ISIN_MAP[raw])

    clean_low = key_or_symbol.strip().lower()
    for alias, root in _ALIAS_MAP.items():
        if alias in clean_low:
            return dict(_ISIN_MAP[root])

    return None
