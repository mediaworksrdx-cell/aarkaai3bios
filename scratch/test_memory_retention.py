import sys
import os

# Add root directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, SessionLocal, UserMemory, PersonalChat
from modules import memory

def test_memory():
    print("Initializing Database...")
    init_db()
    
    user_id = "test_user_rathish_123"
    session_id = "test_session_456"
    
    # Clean up previous runs
    session = SessionLocal()
    session.query(UserMemory).filter(UserMemory.user_id == user_id).delete()
    session.query(PersonalChat).filter(PersonalChat.user_id == user_id).delete()
    session.commit()
    session.close()
    
    print("\n--- Test 1: Fact Extraction ---")
    query_1 = "Hello, my name is Rathish and I live in Bangalore"
    print(f"Query: '{query_1}'")
    
    # Store conversation (triggers extraction via post_process or directly here)
    memory.store_conversation(user_id, session_id, query_1, "Hello Rathish! Nice to meet you.")
    memory.extract_user_facts(user_id, query_1)
    
    # Verify extraction
    facts = memory.get_user_memories(user_id, category="user_fact")
    print("Extracted facts:")
    for fact in facts:
        print(f"  {fact['key']}: {fact['value']}")
        
    assert any(f["key"] == "user_name" and f["value"] == "Rathish" for f in facts), "Name extraction failed"
    assert any(f["key"] == "user_location" and f["value"] == "Bangalore" for f in facts), "Location extraction failed"
    
    print("\n--- Test 2: Facts Prompt Injection Block ---")
    prompt_block = memory.get_user_facts_prompt(user_id)
    print("Generated Prompt Block:")
    print(prompt_block)
    assert "Name: Rathish" in prompt_block, "Name prompt block check failed"
    assert "Location: Bangalore" in prompt_block, "Location prompt block check failed"
    
    print("\n--- Test 3: Multi-turn Chat Context Retrieval ---")
    query_2 = "What is the capital of India?"
    memory.store_conversation(user_id, session_id, query_2, "The capital of India is New Delhi.")
    
    chat_history = memory.get_chat_context(user_id, session_id, limit=10)
    print(f"Chat Context History (last {len(chat_history)} messages):")
    for chat in chat_history:
        print(f"  {chat['role']}: {chat['message']}")
        
    assert len(chat_history) == 4, "Should have 4 messages in history"
    
    print("\nSUCCESS: All memory tests passed locally!")

if __name__ == "__main__":
    test_memory()
