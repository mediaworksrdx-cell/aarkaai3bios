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
    import config
    from modules import memory, rag

    # 1. MongoDB Execution Path
    if config.MONGODB_URI:
        try:
            from modules.mongo_repository import RLHFRepo, ConversationRepo
            last_learned_ts = 0.0
            try:
                memories = memory.get_user_memories(user_id, category="auto_learn_meta")
                for m in memories:
                    if m["key"] == "last_learned_mongo_ts":
                        last_learned_ts = float(m["value"])
                        break
            except Exception as e:
                logger.debug("No last_learned_mongo_ts: %s", e)

            feedbacks = RLHFRepo.get_positive_or_corrected(user_id=user_id, limit=50)
            valid_convs = []
            max_ts = last_learned_ts

            for fb in feedbacks:
                fb_ts = fb.get("timestamp")
                fb_epoch = fb_ts.timestamp() if fb_ts and hasattr(fb_ts, "timestamp") else 0.0
                if fb_epoch <= last_learned_ts:
                    continue
                if fb_epoch > max_ts:
                    max_ts = fb_epoch

                sess_id = fb.get("session_id") or fb.get("conversation_id")
                if sess_id:
                    conv_doc = ConversationRepo.get_latest_by_session(session_id=str(sess_id), user_id=user_id)
                    if not conv_doc:
                        conv_doc = ConversationRepo.get_latest_by_session(session_id=str(sess_id))
                    if conv_doc and conv_doc.get("query") and conv_doc.get("response"):
                        valid_convs.append({
                            "id": str(conv_doc.get("_id", sess_id)),
                            "query": conv_doc.get("query", ""),
                            "response": conv_doc.get("response", ""),
                            "intent": conv_doc.get("intent", "general"),
                            "confidence": conv_doc.get("confidence", 0.9),
                            "source": conv_doc.get("source", "aarkaa-3b"),
                        })

            if valid_convs:
                logger.info(
                    "Auto-learn (Mongo) triggered for user %s on %d feedback conversations",
                    user_id, len(valid_convs)
                )
                knowledge_items = extract_knowledge(valid_convs)
                for item in knowledge_items:
                    rag.store_knowledge(
                        topic=item["topic"],
                        content=item["content"],
                        source="learned_fact",
                        user_id=user_id,
                    )
                update_profile_from_history(user_id, valid_convs)
                memory.update_user_memory(
                    user_id=user_id,
                    key="last_learned_mongo_ts",
                    value=str(max_ts),
                    category="auto_learn_meta",
                )
                logger.info("Auto-learn (Mongo) completed: %d facts stored", len(knowledge_items))
                return True
        except Exception as mongo_err:
            logger.error("Auto-learn Mongo execution failed: %s", mongo_err)

    # 2. SQLite Execution Path
    from database import SessionLocal, ConversationHistory, RLHFFeedback

    last_id = 0
    try:
        memories = memory.get_user_memories(user_id, category="auto_learn_meta")
        for m in memories:
            if m["key"] == "last_learned_conv_id":
                last_id = int(m["value"])
                break
    except Exception as exc:
        logger.error("Failed to read last_learned_conv_id: %s", exc)

    session = SessionLocal()
    try:
        rows = (
            session.query(ConversationHistory)
            .join(RLHFFeedback, ConversationHistory.id == RLHFFeedback.conversation_id)
            .filter(
                ConversationHistory.user_id == user_id,
                ConversationHistory.id > last_id,
                (RLHFFeedback.rating >= 1) | ((RLHFFeedback.correction.isnot(None)) & (RLHFFeedback.correction != ""))
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

    # 3. Implicit Learning Path — confidence-based (no RLHF required)
    # Triggers for high-confidence responses that likely contain useful knowledge
    try:
        from modules import memory, rag
        recent_chats = memory.get_chat_context(user_id, limit=AUTO_LEARN_INTERVAL)
        if not recent_chats:
            return False

        high_conf_convs = []
        for msg in recent_chats:
            role = msg.get("role", "")
            content = msg.get("message") or msg.get("content", "")
            conf = msg.get("confidence", 0.0)
            if role == "assistant" and conf >= 0.85 and len(content) > 200:
                high_conf_convs.append({
                    "id": msg.get("_id", "implicit"),
                    "query": msg.get("query", ""),
                    "response": content,
                    "intent": msg.get("intent", "general"),
                    "confidence": conf,
                    "source": "implicit_learn",
                })

        if high_conf_convs and len(high_conf_convs) >= 3:
            logger.info(
                "Implicit auto-learn triggered for user %s on %d high-confidence responses",
                user_id, len(high_conf_convs)
            )
            knowledge_items = extract_knowledge(high_conf_convs)
            for item in knowledge_items:
                rag.store_knowledge(
                    topic=item["topic"],
                    content=item["content"],
                    source="implicit_learned",
                    user_id=user_id,
                )
            if knowledge_items:
                logger.info("Implicit auto-learn completed: %d facts stored", len(knowledge_items))
                return True
    except Exception as implicit_exc:
        logger.debug("Implicit auto-learn path skipped: %s", implicit_exc)

    return False


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
