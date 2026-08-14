"""
AARKAAI – Architecture Response Verifier
Post-generation verification for architecture-related queries.
Ensures responses reference AARKAA's own internal systems rather than generic external frameworks.
"""
from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

# Terms that indicate the response is discussing external/unrelated systems
_EXTERNAL_SYSTEM_BLOCKLIST = [
    "airflow", "apache airflow", "dag in airflow",
    "postgresql", "postgres",
    "sql planner", "sql query planner", "query optimizer",
    "apache kafka", "kafka",
    "rabbitmq", "rabbit mq",
    "kubernetes scheduler", "k8s scheduler",
    "celery", "celery task",
    "luigi", "luigi pipeline",
    "prefect", "prefect flow",
    "dagster", "dagster pipeline",
    "argo workflow", "argo",
    "tekton", "tekton pipeline",
    "jenkins pipeline", "jenkins",
    "apache beam", "beam pipeline",
    "aws step functions", "step functions",
    "azure data factory",
    "google cloud composer",
]

# Terms that indicate the response IS correctly discussing AARKAA's architecture
_AARKAA_ARCHITECTURE_TERMS = [
    "aarkaa", "aarka",
    "goal planner", "goalplanner",
    "task dag", "taskdag", "tasknode",
    "execution engine",
    "supervisor", "check_loop", "sliding window",
    "reflection", "check_evidence_replanning", "replanning",
    "task memory", "taskmemory", "taskgoal",
    "tool registry", "execute_tool",
    "semantic filter", "domain_prototypes",
    "coordinator", "react loop", "stream_task",
    "pipeline", "process_query",
    "scratchpad", "retry_budget",
    "pydantic", "acyclic", "_is_acyclic",
    "circuit breaker", "_CircuitBreaker",
    "aarkaa-3b", "aarkaa_engine",
    "gguf", "llama_cpp",
    "aarkaa-vision", "aarkaa_vision",
    "chromadb", "chroma",
]


def is_architecture_query(query: str) -> bool:
    """
    Detect if a query is asking about AARKAA's own internal architecture.
    
    Returns True when the query contains AARKAA-specific architecture terms.
    Does NOT trigger for generic system design questions (e.g., "design a scheduler").
    """
    q_low = query.lower()

    # Must mention AARKAA or one of its specific internal component names
    aarkaa_mentions = [
        "aarkaa", "aarka", "aarkaai",
    ]
    component_mentions = [
        "goal planner", "execution engine", "supervisor",
        "reflection", "task memory", "tool registry",
        "coordinator", "semantic filter", "pipeline",
        "planner output", "planner validation",
        "task dag", "react loop", "scratchpad",
        "circuit breaker",
    ]

    has_aarkaa = any(term in q_low for term in aarkaa_mentions)
    has_component = any(term in q_low for term in component_mentions)

    # Require either an explicit AARKAA mention, or a component mention
    # combined with words suggesting they're asking about "your"/"this" system
    if has_aarkaa:
        return True

    if has_component:
        # Check if they're asking about "your" or "this" or "the" system's component
        possessive_markers = [
            "your ", "this ", "the ", "how does the ", "how does your ",
            "explain the ", "explain your ", "what is the ", "what is your ",
            "describe the ", "describe your ", "how do you ", "how do your ",
        ]
        if any(marker in q_low for marker in possessive_markers):
            return True
        # Also trigger if the query is short and focused (just asking about the component)
        if len(query.split()) <= 8:
            return True

    return False


def verify_architecture_response(query: str, response: str) -> bool:
    """
    Verify that a response to an architecture query actually discusses AARKAA's internals.
    
    Returns True if the response is on-topic (references AARKAA components).
    Returns False if the response discusses external/unrelated systems without AARKAA context.
    """
    resp_low = response.lower()

    # Count external system references
    external_hits = sum(1 for term in _EXTERNAL_SYSTEM_BLOCKLIST if term in resp_low)

    # Count AARKAA architecture references
    aarkaa_hits = sum(1 for term in _AARKAA_ARCHITECTURE_TERMS if term in resp_low)

    # If the response has external references but no/few AARKAA references, it's off-topic
    if external_hits >= 2 and aarkaa_hits < 2:
        logger.warning(
            "Architecture verifier REJECTED response: %d external refs, %d AARKAA refs",
            external_hits, aarkaa_hits,
        )
        return False

    # If the response has zero AARKAA references at all, it's likely off-topic
    if aarkaa_hits == 0 and len(response) > 200:
        logger.warning(
            "Architecture verifier REJECTED response: 0 AARKAA refs in %d chars",
            len(response),
        )
        return False

    return True


def build_architecture_repair_prompt(query: str, arch_context: str) -> str:
    """
    Build a strong prompt that forces the model to answer from AARKAA's architecture docs.
    Used when the initial response fails verification.
    """
    return (
        "You are AARKAA, answering a question about YOUR OWN internal architecture. "
        "You MUST answer ONLY from the following AARKAA architecture documentation. "
        "Do NOT reference external systems like Airflow, Kafka, PostgreSQL, Kubernetes, "
        "Jenkins, Celery, or any other third-party framework. "
        "Explain AARKAA's own implementation using the specific class names, function names, "
        "and module names from the documentation below.\n\n"
        "=== AARKAA ARCHITECTURE DOCUMENTATION ===\n"
        f"{arch_context}\n"
        "=== END DOCUMENTATION ===\n\n"
        f"User Question: {query}\n\n"
        "Answer concisely and accurately using ONLY the architecture documentation above:"
    )
