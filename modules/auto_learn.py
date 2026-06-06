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
    Only runs on conversations that have positive RLHF feedback or corrections.
    """
    from modules import memory, rag
    from database import SessionLocal, ConversationHistory, RLHFFeedback

    # 1. Get last learned conversation ID from user memory
    last_id = 0
    try:
        memories = memory.get_user_memories(user_id, category="auto_learn_meta")
        for m in memories:
            if m["key"] == "last_learned_conv_id":
                last_id = int(m["value"])
                break
    except Exception as exc:
        logger.error("Failed to read last_learned_conv_id: %s", exc)

    # 2. Fetch new conversations with positive feedback or corrections
    session = SessionLocal()
    try:
        rows = (
            session.query(ConversationHistory)
            .join(RLHFFeedback, ConversationHistory.id == RLHFFeedback.conversation_id)
            .filter(
                ConversationHistory.user_id == user_id,
                ConversationHistory.id > last_id,
                (RLHFFeedback.rating >= 1) | (RLHFFeedback.correction.isnot(None))
            )
            .order_by(ConversationHistory.id.asc())
            .all()
        )
        if not rows:
            return False

        logger.info(
            "Auto-learn triggered for user %s on %d new feedback conversations",
            user_id, len(rows)
        )

        conversations = [
            {
                "id": r.id,
                "query": r.query,
                "response": r.response,
                "intent": r.intent,
                "confidence": r.confidence,
                "source": r.source,
            }
            for r in rows
        ]

        # 3. Extract knowledge as general factual summaries
        knowledge_items = extract_knowledge(conversations)

        # 4. Store each piece of knowledge as "learned_fact"
        for item in knowledge_items:
            rag.store_knowledge(
                topic=item["topic"],
                content=item["content"],
                source="learned_fact",
                user_id=user_id,
            )

        # 5. Update user profile
        update_profile_from_history(user_id, conversations)

        # 6. Save the new last learned ID
        max_id = max(r.id for r in rows)
        memory.update_user_memory(
            user_id=user_id,
            key="last_learned_conv_id",
            value=str(max_id),
            category="auto_learn_meta"
        )

        logger.info(
            "Auto-learn completed: %d general facts stored for user %s",
            len(knowledge_items),
            user_id,
        )
        return True
    except Exception as exc:
        logger.error("check_and_learn failed: %s", exc)
        return False
    finally:
        session.close()


def extract_knowledge(conversations: list[dict]) -> list[dict]:
    """
    Extract key knowledge from a batch of conversations.
    Uses AARKAA model to synthesize Q&A pairs into general facts.
    """
    from modules.aarkaa_engine import generate_raw

    knowledge_items: list[dict] = []

    # Group conversations by intent/topic
    intent_groups: dict[str, list[dict]] = {}
    for conv in conversations:
        intent = conv.get("intent", "general")
        intent_groups.setdefault(intent, []).append(conv)

    greetings = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "how are you", "who are you"]

    for intent, convs in intent_groups.items():
        qa_pairs = []
        for c in convs:
            q = c["query"]
            a = c["response"]
            if q.lower().strip() in greetings:
                continue
            qa_pairs.append(f"Q: {q}\nA: {a}")

        if not qa_pairs:
            continue

        qa_text = "\n\n".join(qa_pairs)
        
        # Build prompt for LLM to extract clean, general facts
        system_prompt = (
            "You are AARKAA, a factual knowledge extraction system.\n"
            "Your task is to extract clear, general, declarative factual statements or rules from the provided conversation Q&A pairs.\n"
            "Instructions:\n"
            "- Summarize the core lessons, facts, or instructions discussed in the Q&A pairs.\n"
            "- Write only clean, general facts or guidelines.\n"
            "- Do NOT write it as a dialog, Q&A, or raw transcript. Do NOT include 'Q:' or 'A:' or 'The user asked'.\n"
            "- Do NOT refer to 'the user' or 'the assistant'.\n"
            "- Keep it simple, concise, and structured (e.g. bullet points of facts/rules).\n"
            "- If no new or useful general knowledge can be extracted, output 'NONE'."
        )
        prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\nConversation Q&A Pairs:\n{qa_text}<|im_end|>\n<|im_start|>assistant\nExtracted Facts:\n"
        
        try:
            facts = generate_raw(prompt, max_new_tokens=400, stop=["<|im_start|>", "<|im_end|>"])
            facts = facts.strip()
            if facts and facts.upper() != "NONE":
                topics = _extract_topics([qa_text])
                topic_str = ", ".join(topics[:3]) if topics else intent
                knowledge_items.append({
                    "topic": f"Learned: {topic_str}",
                    "content": facts[:2000],
                })
        except Exception as exc:
            logger.error("Failed to extract facts using generate_raw: %s", exc)

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
