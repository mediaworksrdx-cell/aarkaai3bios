"""
AARKAAI – Semantic Filter (TensorFlow + SKLearn)

Classifies incoming queries into domains, scores confidence,
and refines intent for downstream routing.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np

from config import CONFIDENCE_THRESHOLD, DOMAIN_LABELS, EMBEDDING_DIM

logger = logging.getLogger(__name__)

# ─── Lazy globals (set on init) ───────────────────────────────────────────────
_tf_model: Optional[object] = None
_sklearn_scaler: Optional[object] = None
_domain_prototypes: Optional[np.ndarray] = None
_embedding_fn = None  # callable(text) → np.ndarray


# ─── Domain keyword heuristics (bootstrap / fallback) ────────────────────────
_DOMAIN_KEYWORDS: dict[str, list[str]] = {
    "finance": [
        # English
        "stock", "price", "market", "share", "crypto", "bitcoin", "forex",
        "commodity", "gold", "silver", "oil", "nifty", "sensex", "nasdaq",
        "trading", "investment", "dividend", "portfolio", "etf", "mutual fund",
        "bull", "bear", "ipo", "ticker", "earnings", "revenue",
        # Hindi
        "शेयर", "बाजार", "कीमत", "सोना", "चांदी", "निवेश", "मुनाफा",
        # Spanish
        "acciones", "mercado", "precio", "inversión", "bolsa", "comercio",
        # French
        "bourse", "marché", "investissement", "actions", "dividende",
        # German
        "aktie", "markt", "investition", "börse", "handel",
        # Arabic
        "سوق", "أسهم", "استثمار", "ذهب", "تداول",
        # Japanese
        "株", "市場", "投資", "金", "取引",
        # Chinese
        "股票", "市场", "投资", "黄金", "交易",
    ],
    "technology": [
        # English
        "python", "java", "code", "programming", "software", "hardware",
        "ai", "machine learning", "deep learning", "neural", "algorithm",
        "api", "cloud", "database", "framework", "linux", "windows",
        "docker", "kubernetes", "devops", "cybersecurity", "blockchain",
        # Hindi
        "कोड", "प्रोग्रामिंग", "तकनीक", "सॉफ्टवेयर", "कंप्यूटर",
        # Spanish
        "programación", "tecnología", "código", "computadora", "red",
        # French
        "programmation", "technologie", "logiciel", "ordinateur", "réseau",
        # German
        "programmierung", "technologie", "rechner", "netzwerk",
        # Arabic
        "برمجة", "تقنية", "حاسوب", "شبكة",
        # Japanese
        "プログラミング", "技術", "コンピュータ", "ソフトウェア",
        # Chinese
        "编程", "技术", "计算机", "软件", "网络",
    ],
    "science": [
        # English
        "physics", "chemistry", "biology", "quantum", "atom", "molecule",
        "dna", "evolution", "gravity", "relativity", "thermodynamics",
        "experiment", "hypothesis", "theory", "research", "astronomy",
        "planet", "star", "galaxy", "cell", "organism", "ecosystem",
        # Hindi
        "भौतिकी", "रसायन", "जीवविज्ञान", "अनुसंधान", "प्रयोग", "विज्ञान",
        # Spanish
        "física", "química", "biología", "ciencia", "experimento", "investigación",
        # French
        "physique", "chimie", "biologie", "expérience", "recherche", "science",
        # German
        "physik", "chemie", "biologie", "wissenschaft", "forschung",
        # Arabic
        "فيزياء", "كيمياء", "أحياء", "علم", "بحث",
        # Japanese
        "物理", "化学", "生物", "科学", "研究", "実験",
        # Chinese
        "物理", "化学", "生物", "科学", "研究", "实验",
    ],
    "health": [
        # English
        "health", "medical", "disease", "symptom", "treatment", "medicine",
        "doctor", "hospital", "surgery", "vaccine", "nutrition", "diet",
        "exercise", "mental health", "therapy", "diagnosis", "virus",
        "bacteria", "infection", "blood pressure", "diabetes", "cancer",
        # Hindi
        "स्वास्थ्य", "बीमारी", "इलाज", "डॉक्टर", "अस्पताल", "दवा",
        # Spanish
        "salud", "enfermedad", "tratamiento", "médico", "hospital", "medicina",
        # French
        "santé", "maladie", "traitement", "médecin", "hôpital", "médicament",
        # German
        "gesundheit", "krankheit", "behandlung", "arzt", "krankenhaus",
        # Arabic
        "صحة", "مرض", "علاج", "طبيب", "مستشفى",
        # Japanese
        "健康", "病気", "治療", "医者", "病院", "薬",
        # Chinese
        "健康", "疾病", "治疗", "医生", "医院", "药物",
    ],
    "history": [
        # English
        "history", "war", "ancient", "civilization", "empire", "dynasty",
        "revolution", "independence", "king", "queen", "medieval", "colonial",
        "century", "archaeological", "artifact", "historical", "era",
        "renaissance", "industrial revolution", "world war",
        # Hindi
        "इतिहास", "युद्ध", "सभ्यता", "साम्राज्य", "स्वतंत्रता", "राजा",
        # Spanish
        "historia", "guerra", "civilización", "imperio", "revolución",
        # French
        "histoire", "guerre", "civilisation", "empire", "révolution",
        # German
        "geschichte", "krieg", "zivilisation", "reich", "revolution",
        # Arabic
        "تاريخ", "حرب", "حضارة", "إمبراطورية", "ثورة",
        # Japanese
        "歴史", "戦争", "文明", "帝国", "革命",
        # Chinese
        "历史", "战争", "文明", "帝国", "革命",
    ],
    "web_search": [
        # English
        "latest", "news", "current", "today", "update", "recent",
        "trending", "breaking", "live", "happening", "2024", "2025", "2026",
        # Hindi
        "ताज़ा", "समाचार", "आज", "खबर", "अपडेट",
        # Spanish
        "noticias", "hoy", "actual", "último", "actualización",
        # French
        "nouvelles", "aujourd'hui", "actuel", "dernier", "actualité",
        # German
        "nachrichten", "heute", "aktuell", "neueste",
        # Arabic
        "أخبار", "اليوم", "آخر", "عاجل",
        # Japanese
        "ニュース", "最新", "今日", "速報",
        # Chinese
        "新闻", "最新", "今天", "头条",
    ],
}


def _keyword_scores(query: str) -> dict[str, float]:
    """Simple keyword-overlap scoring for bootstrap."""
    q_lower = query.lower()
    scores: dict[str, float] = {}
    for domain, keywords in _DOMAIN_KEYWORDS.items():
        hits = sum(1 for kw in keywords if kw in q_lower)
        scores[domain] = hits / max(len(keywords), 1)
    # general gets a baseline
    scores["general"] = 0.3
    return scores


# ─── TensorFlow model builder ────────────────────────────────────────────────


def _build_tf_classifier(input_dim: int = EMBEDDING_DIM, n_classes: int = len(DOMAIN_LABELS)):
    """Build a small dense classifier for domain routing."""
    try:
        import tensorflow as tf

        model = tf.keras.Sequential(
            [
                tf.keras.layers.Input(shape=(input_dim,)),
                tf.keras.layers.Dense(128, activation="relu"),
                tf.keras.layers.Dropout(0.3),
                tf.keras.layers.Dense(64, activation="relu"),
                tf.keras.layers.Dropout(0.2),
                tf.keras.layers.Dense(n_classes, activation="softmax"),
            ]
        )
        model.compile(
            optimizer="adam",
            loss="sparse_categorical_crossentropy",
            metrics=["accuracy"],
        )
        logger.info("TensorFlow domain classifier built (%d → %d)", input_dim, n_classes)
        return model
    except Exception as exc:
        logger.warning("Could not build TF classifier: %s", exc)
        return None


# ─── SKLearn scaler ───────────────────────────────────────────────────────────


def _build_sklearn_scaler():
    """MinMax scaler to normalize TF outputs."""
    try:
        from sklearn.preprocessing import MinMaxScaler

        scaler = MinMaxScaler()
        # Fit with a dummy range so it can transform immediately
        dummy = np.array([[0.0] * len(DOMAIN_LABELS), [1.0] * len(DOMAIN_LABELS)])
        scaler.fit(dummy)
        logger.info("SKLearn MinMaxScaler ready")
        return scaler
    except Exception as exc:
        logger.warning("Could not build SK scaler: %s", exc)
        return None


# ─── Domain prototype embeddings ─────────────────────────────────────────────


def _build_domain_prototypes(embed_fn) -> np.ndarray:
    """
    Create a prototype embedding for each domain by averaging
    the embeddings of its keywords.
    """
    prototypes = []
    for domain in DOMAIN_LABELS:
        keywords = _DOMAIN_KEYWORDS.get(domain, [domain])
        vecs = [embed_fn(kw) for kw in keywords[:10]]  # limit for speed
        prototypes.append(np.mean(vecs, axis=0))
    return np.array(prototypes)


# ─── Public API ───────────────────────────────────────────────────────────────


def init(embed_fn) -> None:
    """
    Initialise the semantic filter.

    Parameters
    ----------
    embed_fn : callable
        A function  text → np.ndarray(384,)  that produces embeddings.
    """
    global _tf_model, _sklearn_scaler, _domain_prototypes, _embedding_fn
    _embedding_fn = embed_fn
    _tf_model = _build_tf_classifier()
    _sklearn_scaler = _build_sklearn_scaler()
    try:
        _domain_prototypes = _build_domain_prototypes(embed_fn)
        logger.info("Domain prototypes built for %d domains", len(DOMAIN_LABELS))
    except Exception as exc:
        logger.warning("Could not build domain prototypes: %s", exc)
        _domain_prototypes = None


def classify(query: str) -> dict:
    """
    Classify a query into a domain with confidence.

    Returns
    -------
    dict with keys: domain, confidence, intent, scores
    """
    scores: dict[str, float] = {}

    # 1. Keyword heuristic scores
    kw_scores = _keyword_scores(query)

    # 2. Embedding-based cosine similarity against prototypes
    proto_scores: dict[str, float] = {}
    if _embedding_fn is not None and _domain_prototypes is not None:
        try:
            q_vec = _embedding_fn(query)
            # Cosine similarity
            norms = np.linalg.norm(_domain_prototypes, axis=1) * np.linalg.norm(q_vec)
            norms = np.where(norms == 0, 1e-10, norms)
            sims = _domain_prototypes @ q_vec / norms
            for idx, domain in enumerate(DOMAIN_LABELS):
                proto_scores[domain] = float(sims[idx])
        except Exception as exc:
            logger.warning("Prototype scoring failed: %s", exc)

    # 3. TensorFlow neural scoring
    tf_scores: dict[str, float] = {}
    if _tf_model is not None and _embedding_fn is not None:
        try:
            q_vec = _embedding_fn(query).reshape(1, -1)
            preds = _tf_model.predict(q_vec, verbose=0)[0]
            for idx, domain in enumerate(DOMAIN_LABELS):
                tf_scores[domain] = float(preds[idx])
        except Exception as exc:
            logger.warning("TF scoring failed: %s", exc)

    # 4. Fuse scores (weighted combination)
    for domain in DOMAIN_LABELS:
        kw = kw_scores.get(domain, 0.0)
        proto = proto_scores.get(domain, 0.0)
        tf = tf_scores.get(domain, 0.0)

        # Weight: prototype > TF > keyword (prototype is most reliable pre-training)
        if proto_scores and tf_scores:
            scores[domain] = 0.45 * proto + 0.35 * tf + 0.20 * kw
        elif proto_scores:
            scores[domain] = 0.65 * proto + 0.35 * kw
        else:
            scores[domain] = kw

    # 5. SKLearn normalization
    if _sklearn_scaler is not None and scores:
        try:
            vals = np.array([[scores[d] for d in DOMAIN_LABELS]])
            normed = _sklearn_scaler.transform(vals)[0]
            for idx, domain in enumerate(DOMAIN_LABELS):
                scores[domain] = float(normed[idx])
        except Exception:
            pass  # keep raw scores

    # 6. Pick best
    if scores:
        best_domain = max(scores, key=scores.get)  # type: ignore[arg-type]
        confidence = scores[best_domain]
    else:
        best_domain = "general"
        confidence = 0.5

    intent = _refine_intent(query, best_domain)

    return {
        "domain": best_domain,
        "confidence": float(confidence),
        "intent": intent,
        "scores": {k: round(v, 4) for k, v in scores.items()},
    }


def _refine_intent(query: str, domain: str) -> str:
    """Determine sub-intent within a domain."""
    q = query.lower()

    if domain == "finance":
        if any(w in q for w in ["price", "quote", "value", "how much"]):
            return "price_check"
        if any(w in q for w in ["news", "latest", "update"]):
            return "finance_news"
        if any(w in q for w in ["compare", "vs", "versus"]):
            return "comparison"
        return "finance_general"

    if domain == "web_search":
        if any(w in q for w in ["news", "breaking", "headline"]):
            return "news_search"
        return "web_lookup"

    if domain == "technology":
        if any(w in q for w in ["code", "program", "function", "error", "bug", "debug"]):
            return "coding_help"
        return "tech_info"

    return f"{domain}_query"


def retrain(training_data: list[dict]) -> bool:
    """
    Retrain the TF classifier on accumulated labelled data.

    Parameters
    ----------
    training_data : list of dict
        Each dict must have 'embedding' (list[float]) and 'label_index' (int).

    Returns
    -------
    bool – True if training succeeded.
    """
    if _tf_model is None or not training_data:
        return False

    try:
        X = np.array([d["embedding"] for d in training_data])
        y = np.array([d["label_index"] for d in training_data])
        _tf_model.fit(X, y, epochs=5, batch_size=16, verbose=0)
        logger.info("Semantic filter retrained on %d samples", len(training_data))
        return True
    except Exception as exc:
        logger.warning("Retrain failed: %s", exc)
        return False
