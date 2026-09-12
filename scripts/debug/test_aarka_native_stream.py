import os
import sys
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

sys.path.insert(0, "/home/mediaworksr/aarkaai3b")
from modules import aarkaa_engine

def test_native_aarka():
    print("=" * 60)
    print("Testing Native Aarka Neural Engine (GGUF)")
    print("=" * 60)

    if not aarkaa_engine.is_available():
        print("Initializing Aarka engine...")
        aarkaa_engine.init()

    print(f"Engine available: {aarkaa_engine.is_available()}")
    print(f"Active model path: {getattr(aarkaa_engine, '_model_path', 'N/A')}")

    history = [
        {"role": "user", "content": "My secret project code is Project Nebula and target valuation is 50 million dollars."},
        {"role": "assistant", "content": "Understood! Project Nebula with target valuation 50 million dollars has been recorded."},
        {"role": "user", "content": "What is the primary database we are using?"},
        {"role": "assistant", "content": "We are using MongoDB with ChromaDB for semantic vector retrieval."},
        {"role": "user", "content": "What about the streaming architecture?"},
        {"role": "assistant", "content": "We are using Apache Kafka with Flink for stream processing."},
        {"role": "user", "content": "Is the infrastructure hosted on GCP or AWS?"},
        {"role": "assistant", "content": "The infrastructure is deployed on GCP compute instances."},
        {"role": "user", "content": "What is the primary LLM engine?"},
        {"role": "assistant", "content": "The primary engine is the native Aarka neural model running locally via llama.cpp."}
    ]

    query = "Now tell me, what was the secret project code and target valuation I told you in the very beginning?"
    print(f"\nPrompting Native Aarka Engine with {len(history)} prior messages:")
    prompt, max_tok, temp = aarkaa_engine._build_final_prompt(
        query=query,
        context="",
        intent="general_query",
        history=history
    )
    print(f"PROMPT LENGTH: {len(prompt)} chars")
    print(f"PROMPT TOKENS LIMIT: {max_tok}")
    print(f"PROMPT TEMPERATURE: {temp}")
    print("--- PROMPT START ---")
    print(prompt)
    print("--- PROMPT END ---")

    print("Streaming native model tokens:")
    print("-" * 40)

    tokens = []
    for token in aarkaa_engine.stream_final_response(
        query=query,
        context="",
        intent="general_query",
        history=history
    ):
        tokens.append(token)
        sys.stdout.write(token)
        sys.stdout.flush()

    print("\n" + "-" * 40)
    full_text = "".join(tokens)

    recalled_nebula = "nebula" in full_text.lower()
    recalled_valuation = "50" in full_text.lower()

    print("\nVerification Results:")
    print(f"  Recalled Project Nebula: {recalled_nebula}")
    print(f"  Recalled 50 million:     {recalled_valuation}")

    if recalled_nebula and recalled_valuation:
        print("\nSUCCESS: Native Aarka Neural Engine accurately recalled 10-message conversational context!")
    else:
        print("\nWARNING: One or more facts were missing from the response.")

if __name__ == "__main__":
    test_native_aarka()
