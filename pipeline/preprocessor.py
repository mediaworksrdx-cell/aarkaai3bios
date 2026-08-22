"""
AARKAAI Backend – Input Preprocessing

Handles input normalization, language detection, query sanitization,
and initial classification before routing.
"""
from __future__ import annotations

import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def normalize_query(query: str) -> str:
    """Normalize whitespace, strip control characters, and clean input."""
    if not query:
        return ""
    # Collapse whitespace
    cleaned = re.sub(r'\s+', ' ', query).strip()
    # Remove null bytes and other dangerous control chars
    cleaned = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', cleaned)
    return cleaned


def detect_language(text: str) -> str:
    """Detect the primary language of the input text.
    
    Returns ISO 639-1 code (e.g., 'en', 'hi', 'ta').
    Falls back to 'en' if detection fails.
    """
    try:
        # Use simple heuristic: check for non-ASCII script blocks
        # Tamil Unicode range: 0B80-0BFF
        tamil_count = sum(1 for c in text if '\u0B80' <= c <= '\u0BFF')
        # Devanagari Unicode range: 0900-097F  
        hindi_count = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        
        total = len(text)
        if total == 0:
            return 'en'
        
        if tamil_count / total > 0.3:
            return 'ta'
        if hindi_count / total > 0.3:
            return 'hi'
        return 'en'
    except Exception:
        return 'en'


def extract_mentions(query: str) -> dict:
    """Extract structured mentions from the query.
    
    Returns dict with keys: tickers, urls, file_paths, @mentions.
    """
    result = {
        "tickers": [],
        "urls": [],
        "file_paths": [],
        "mentions": [],
    }
    
    # Stock tickers (e.g., $AAPL, RELIANCE.NS)
    tickers = re.findall(r'\$([A-Z]{1,5})', query)
    tickers += re.findall(r'\b([A-Z]{2,5}\.NS)\b', query)
    result["tickers"] = list(set(tickers))
    
    # URLs
    urls = re.findall(r'https?://[^\s<>"]+', query)
    result["urls"] = urls
    
    # File paths
    paths = re.findall(r'(?:[a-zA-Z]:\\|/)[^\s<>"]+', query)
    result["file_paths"] = paths
    
    return result
