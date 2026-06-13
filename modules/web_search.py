"""
AARKAAI – Web Search Module (DuckDuckGo + Wikipedia)

Used when latest information is required or RAG is insufficient.
"""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ─── DuckDuckGo ───────────────────────────────────────────────────────────────


def search_ddg(query: str, max_results: int = 5) -> list[dict]:
    """
    Search DuckDuckGo for web results.

    Returns list of dicts with keys: title, url, snippet
    """
    try:
        from ddgs import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", r.get("link", "")),
                    "snippet": r.get("body", r.get("snippet", "")),
                })
        logger.info("DDG returned %d results for: %s", len(results), query[:60])
        return results
    except Exception as exc:
        logger.error("DDG search failed: %s", exc)
        return []


# ─── Wikipedia ────────────────────────────────────────────────────────────────


def search_wikipedia(query: str, sentences: int = 5, lang: str = "en") -> Optional[str]:
    """
    Fetch a Wikipedia summary for the query.

    Parameters
    ----------
    lang : str
        ISO 639-1 language code (e.g., 'en', 'hi', 'es', 'fr').

    Returns the summary text, or None if not found.
    """
    try:
        import wikipediaapi

        wiki = wikipediaapi.Wikipedia(
            user_agent="AARKAAI/1.0 (https://aarkaai.local)",
            language=lang,
        )
        page = wiki.page(query)

        if not page.exists() and lang != "en":
            wiki_en = wikipediaapi.Wikipedia(
                user_agent="AARKAAI/1.0 (https://aarkaai.local)",
                language="en",
            )
            page = wiki_en.page(query)

        if page.exists():
            summary = page.summary
            # Truncate to requested sentence count
            sents = summary.split(". ")
            truncated = ". ".join(sents[:sentences])
            if not truncated.endswith("."):
                truncated += "."
            logger.info("Wikipedia match: %s (%d chars, lang=%s)", page.title, len(truncated), lang)
            return f"[Wikipedia: {page.title}]\n{truncated}"

        return None
    except Exception as exc:
        logger.error("Wikipedia search failed: %s", exc)
        return None


import re

def _is_live_tracker_snippet(text: str) -> bool:
    """Detect if a snippet or title looks like a live stock/crypto ticker or widget."""
    s_low = text.lower()
    live_patterns = [
        "price today is", "live price", "current price", "price as of",
        "trading volume", "market cap of", "market capitalization",
        "24-hour volume", "circulating supply", "max supply"
    ]
    if any(p in s_low for p in live_patterns):
        return True
    # Match percentage changes commonly found in live tickers, e.g. -1.09%, +2.5%
    if re.search(r"[-+]\d+(\.\d+)?%", s_low):
        return True
    return False


def get_web_context(query: str, max_results: int = 5, lang: str = "en", filter_live: bool = False) -> str:
    """
    Combined search: DDG + Wikipedia.
    Returns a formatted context string.

    Parameters
    ----------
    lang : str
        ISO 639-1 language code for Wikipedia (e.g., 'hi', 'ja', 'fr').
    filter_live : bool
        If True, filters out live stock/crypto tracker snippets.
    """
    parts: list[str] = []

    # 1. Search DuckDuckGo first to find the most relevant pages and Wikipedia links
    ddg_results = search_ddg(query, max_results=max_results)

    # 2. Extract Wikipedia page title if present in DDG results
    wiki_title = None
    wiki_lang = lang
    if ddg_results:
        from urllib.parse import urlparse, unquote
        for r in ddg_results:
            url = r.get("url", "")
            parsed = urlparse(url)
            if "wikipedia.org" in parsed.netloc:
                # e.g., https://en.wikipedia.org/wiki/Trisha_Krishnan
                path_parts = parsed.path.split("/wiki/")
                if len(path_parts) > 1:
                    wiki_title = unquote(path_parts[1]).split("#")[0].replace("_", " ")
                    netloc_parts = parsed.netloc.split(".")
                    if netloc_parts and len(netloc_parts[0]) == 2:
                        wiki_lang = netloc_parts[0]
                    break

    # 3. Fetch Wikipedia summary
    wiki_context = None
    if wiki_title:
        logger.info("Found Wikipedia link in search results: %s (lang=%s)", wiki_title, wiki_lang)
        wiki_context = search_wikipedia(wiki_title, lang=wiki_lang)

    # Fallback to searching with the query if no Wikipedia link was found in DDG results
    if not wiki_context:
        wiki_context = search_wikipedia(query, lang=lang)

    if wiki_context:
        parts.append(wiki_context)

    # 4. Format DuckDuckGo results
    if ddg_results:
        filtered_results = []
        for r in ddg_results:
            # Skip live stock tickers if requested
            if filter_live and (_is_live_tracker_snippet(r["snippet"]) or _is_live_tracker_snippet(r["title"])):
                logger.info("Filtered out live tracker snippet from web search: %s", r["title"])
                continue
            # Also skip the Wikipedia result we already summarized to avoid duplication
            if "wikipedia.org" in r.get("url", ""):
                continue
            filtered_results.append(r)

        if filtered_results:
            ddg_text = "\n".join(
                f"• [{r['title']}]({r['url']}): {r['snippet']}"
                for r in filtered_results
            )
            parts.append(f"[Web Search Results]\n{ddg_text}")

    return "\n\n---\n\n".join(parts) if parts else ""

