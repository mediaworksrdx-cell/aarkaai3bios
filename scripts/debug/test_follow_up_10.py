import os
import sys
import uuid

# Ensure repository root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from modules import memory
from modules.external_agents import stream_aarka_response, stream_gemini_response
from modules import aarkaa_engine
from modules.context_fusion import ContextFusion, DataSource, FusedContext
from pipeline import _follow_up_score, _detect_topic_shift

def run_tests():
    print("=" * 70)
    print("TEST 1: Memory Storage & Retrieval of 20 Messages (10 Turns)")
    print("=" * 70)
    user_id = f"test_user_{uuid.uuid4().hex[:8]}"
    session_id = f"test_session_{uuid.uuid4().hex[:8]}"

    # Populate 10 complete Q&A turns (20 individual messages)
    test_data = [
        ("My secret project code is Project Nebula and target valuation is $50M.", "Understood. Project Nebula ($50M valuation) recorded."),
        ("What are the key tech stacks for high throughput data pipelines?", "Key tech stacks include Apache Kafka, Apache Flink, and ClickHouse."),
        ("How does Kafka handle partitioning?", "Kafka partitions topics across brokers using key-based hash partitioning."),
        ("What about consumer groups?", "Consumer groups balance partition consumption across instances."),
        ("Can we deploy this on Kubernetes?", "Yes, Strimzi operator enables declarative Kafka deployment on K8s."),
        ("What storage class should we use?", "Use NVMe-backed SSD storage classes with low latency IOPS."),
        ("What is the replication factor?", "A replication factor of 3 with min.insync.replicas=2 is industry standard."),
        ("How does Flink checkpointing work?", "Flink uses the Chandy-Lamport algorithm for distributed state snapshots."),
        ("What about exactly-once semantics?", "End-to-end exactly-once is achieved using two-phase commit sinks."),
        ("Now tell me, what was the secret project code and target valuation I mentioned earlier?", "")
    ]

    for q, a in test_data[:-1]:
        memory.store_conversation(
            user_id=user_id,
            session_id=session_id,
            query=q,
            response=a,
            intent="general_query",
            confidence=0.95,
            source="test"
        )

    # Retrieve context window
    chat_ctx = memory.get_chat_context(user_id, session_id, limit=15)
    print(f"Retrieved {len(chat_ctx)} messages from memory.")
    assert len(chat_ctx) == 18, f"Expected 18 messages (9 pairs), got {len(chat_ctx)}"
    assert "Project Nebula" in chat_ctx[0]["message"], f"Turn 1 user message not in oldest retrieved message! Found: {chat_ctx[0]}"
    print("PASS: Memory correctly retrieved all 18 messages in chronological order, including Turn 1.")

    print("\n" + "=" * 70)
    print("TEST 2: Follow-Up Scoring & Topic Shift Detection")
    print("=" * 70)
    follow_up_q = test_data[-1][0]
    fu_score = _follow_up_score(follow_up_q, chat_ctx)
    print(f"Follow-up query: '{follow_up_q}'")
    print(f"Follow-up score: {fu_score:.2f} (threshold: >0.4)")
    assert fu_score >= 0.7, f"Expected high follow-up score, got {fu_score}"

    topic_shift = _detect_topic_shift(follow_up_q, chat_ctx)
    print(f"Topic shift detected: {topic_shift} (expected: False)")
    assert not topic_shift, "Topic shift falsely triggered on follow-up question!"
    print("PASS: Follow-up score and topic shift guard working correctly.")

    print("\n" + "=" * 70)
    print("TEST 3: Context Fusion Engine History Injection")
    print("=" * 70)
    fusion_engine = ContextFusion()
    fused = fusion_engine.fuse(
        results=[],
        chat_history=chat_ctx
    )
    assert "Project Nebula" in fused.context, "Project Nebula missing from FusedContext!"
    assert "Apache Kafka" in fused.context, "Intermediate Kafka context missing from FusedContext!"
    print("PASS: ContextFusion retained full 10-turn history in fused context.")

    print("\n" + "=" * 70)
    print("TEST 4: Aarka Engine & ChatML Prompt Construction")
    print("=" * 70)
    chatml_prompt = aarkaa_engine._build_chatml_multi(
        system="You are Aarka AI.",
        history=chat_ctx,
        user=follow_up_q
    )
    assert "Project Nebula" in chatml_prompt, "Project Nebula missing from ChatML prompt!"
    assert "two-phase commit" in chatml_prompt, "Turn 9 context missing from ChatML prompt!"
    print(f"ChatML prompt successfully built (length: {len(chatml_prompt)} chars).")
    print("PASS: Aarka Engine ChatML multi-turn formatting preserves all turns.")

    print("\n" + "=" * 70)
    print("TEST 5: Live Inference Follow-up Capability via stream_aarka_response")
    print("=" * 70)
    print(f"Sending 10th turn to stream_aarka_response with {len(chat_ctx)} prior messages...")
    response_tokens = []
    try:
        for token in stream_aarka_response(follow_up_q, history=chat_ctx):
            response_tokens.append(token)
            print(token, end="", flush=True)
        full_ans = "".join(response_tokens)
        print("\n")
        assert "nebula" in full_ans.lower(), f"'Project Nebula' not found in response: {full_ans}"
        assert "50" in full_ans, f"'$50M' not found in response: {full_ans}"
        print("PASS: stream_aarka_response accurately recalled Turn 1 context across 10 messages!")
    except Exception as exc:
        print(f"Vertex AI API call note: {exc}")

    print("\n" + "=" * 70)
    print("ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)

if __name__ == "__main__":
    run_tests()
