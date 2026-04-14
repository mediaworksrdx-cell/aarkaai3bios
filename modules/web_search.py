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

        if not page.exists():
            # Try to search with simplified terms (maximum 3 attempts to avoid excessive HTTP requests)
            words = query.split()
            max_attempts = min(3, len(words))
            for i in range(max_attempts, 0, -1):
                candidate = " ".join(words[:i])
                page = wiki.page(candidate)
                if page.exists():
                    break

        # If still not found and not English, try English as fallback
        if not page.exists() and lang != "en":
            wiki_en = wikipediaapi.Wikipedia(
                user_agent="AARKAAI/1.0 (https://aarkaai.local)",
                language="en",
            )
            page = wiki_en.page(query)
            if not page.exists():
                words = query.split()
                max_attempts = min(3, len(words))
                for i in range(max_attempts, 0, -1):
                    candidate = " ".join(words[:i])
                    page = wiki_en.page(candidate)
                    if page.exists():
                        break

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


# ─── Combined search ─────────────────────────────────────────────────────────


def get_web_context(query: str, max_results: int = 5, lang: str = "en") -> str:
    """
    Combined search: DDG + Wikipedia.
    Returns a formatted context string.

    Parameters
    ----------
    lang : str
        ISO 639-1 language code for Wikipedia (e.g., 'hi', 'ja', 'fr').
    """
    parts: list[str] = []

    # Wikipedia first (authoritative, in user's language if possible)
    wiki = search_wikipedia(query, lang=lang)
    if wiki:
        parts.append(wiki)

    # DuckDuckGo for broader results
    ddg_results = search_ddg(query, max_results=max_results)
    if ddg_results:
        ddg_text = "\n".join(
            f"• [{r['title']}]({r['url']}): {r['snippet']}"
            for r in ddg_results
        )
        parts.append(f"[Web Search Results]\n{ddg_text}")

    return "\n\n---\n\n".join(parts) if parts else ""
