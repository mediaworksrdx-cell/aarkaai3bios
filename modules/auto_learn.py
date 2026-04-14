"""
AARKAAI – Auto-Learning System

Triggered every AUTO_LEARN_INTERVAL messages.
Extracts knowledge from recent conversations, embeds and
stores it in the knowledge base, and updates the user profile.
"""
from __future__ import annotations

import json
import logging
import re
from collections import Counter

from config import AUTO_LEARN_INTERVAL, DOMAIN_LABELS

logger = logging.getLogger(__name__)

# ─── Lazy globals ─────────────────────────────────────────────────────────────
_embedding_fn = None


def init(embed_fn) -> None:
    global _embedding_fn
    _embedding_fn = embed_fn
    logger.info("Auto-learn system initialised (interval=%d)", AUTO_LEARN_INTERVAL)


# ─── Public API ───────────────────────────────────────────────────────────────


def check_and_learn(user_id: str) -> bool:
    """
    Check if auto-learning should trigger and execute if so.

    Returns True if learning was performed.
    """
    from modules import memory, rag

    count = memory.get_conversation_count(user_id)
    if count == 0 or count % AUTO_LEARN_INTERVAL != 0:
        return False

    logger.info(
        "Auto-learn triggered for user %s (conversation #%d)", user_id, count
    )

    # 1. Fetch last N conversations
    conversations = memory.get_recent_conversations(user_id, limit=AUTO_LEARN_INTERVAL)
    if not conversations:
        return False

    # 2. Extract knowledge
    knowledge_items = extract_knowledge(conversations)

    # 3. Store each piece of knowledge
    for item in knowledge_items:
        rag.store_knowledge(
            topic=item["topic"],
            content=item["content"],
            source="auto_learn",
        )

    # 4. Update user profile
    update_profile_from_history(user_id, conversations)

    logger.info(
        "Auto-learn completed: %d knowledge items stored for user %s",
        len(knowledge_items),
        user_id,
    )
    return True


def extract_knowledge(conversations: list[dict]) -> list[dict]:
    """
    Extract key knowledge from a batch of conversations.

    Uses heuristic extraction:
    - Identifies main topics discussed
    - Summarises Q&A pairs into knowledge entries
    - Groups related conversations
    """
    knowledge_items: list[dict] = []

    # Group conversations by intent
    intent_groups: dict[str, list[dict]] = {}
    for conv in conversations:
        intent = conv.get("intent", "general")
        intent_groups.setdefault(intent, []).append(conv)

    for intent, convs in intent_groups.items():
        # Build a combined knowledge entry per intent group
        queries = [c["query"] for c in convs]
        responses = [c["response"] for c in convs]

        # Extract key topics from queries
        topics = _extract_topics(queries)
        topic_str = ", ".join(topics[:5]) if topics else intent

        # Combine Q&A into a knowledge document
        qa_pairs = []
        for q, a in zip(queries, responses):
            # Skip stub responses
            if "[Stub]" in a:
                continue
            qa_pairs.append(f"Q: {q}\nA: {a}")

        if qa_pairs:
            content = f"Topic area: {topic_str}\n\n" + "\n\n".join(qa_pairs)
            knowledge_items.append({
                "topic": f"Learned: {topic_str}",
                "content": content[:2000],  # cap length
            })

    return knowledge_items


def update_profile_from_history(user_id: str, conversations: list[dict]) -> None:
    """Update the user's knowledge profile based on recent conversations."""
    from modules import memory

    # Extract interests from queries
    all_queries = " ".join(c.get("query", "") for c in conversations)
    topics = _extract_topics([all_queries])

    # Determine expertise areas from intents
    intents = [c.get("intent", "general") for c in conversations]
    intent_counts = Counter(intents)
    top_intents = [
        intent for intent, _ in intent_counts.most_common(3) if intent != "general"
    ]

    memory.update_user_profile(
        user_id=user_id,
        interests=topics[:10],
        expertise_areas=top_intents,
        increment_count=False,
    )


def _extract_topics(texts: list[str]) -> list[str]:
    """
    Simple keyword-based topic extraction.
    Finds significant nouns / noun-phrases from text.
    Supports multilingual text (Unicode-aware).
    """
    # Common stop words to filter out (English)
    stop_words = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "shall", "can", "need", "dare", "ought",
        "used", "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "out", "off", "over", "under", "again",
        "further", "then", "once", "here", "there", "when", "where", "why",
        "how", "all", "both", "each", "few", "more", "most", "other",
        "some", "such", "no", "nor", "not", "only", "own", "same", "so",
        "than", "too", "very", "just", "because", "but", "and", "or", "if",
        "while", "about", "what", "which", "who", "whom", "this", "that",
        "these", "those", "i", "me", "my", "myself", "we", "our", "you",
        "your", "he", "him", "his", "she", "her", "it", "its", "they",
        "them", "their", "tell", "explain", "describe", "give", "show",
        "much", "many",
    }

    combined = " ".join(texts).lower()
    # Use Unicode-aware regex: keep word characters (letters, digits, underscore)
    # from ANY script, plus spaces. This preserves Hindi, Chinese, Arabic, etc.
    cleaned = re.sub(r"[^\w\s]", " ", combined, flags=re.UNICODE)
    words = cleaned.split()

    # Filter and count
    meaningful = [w for w in words if w not in stop_words and len(w) > 1]
    counts = Counter(meaningful)

    # Return most common
    return [word for word, _ in counts.most_common(15)]
