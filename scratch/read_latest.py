from database import SessionLocal, ConversationHistory

session = SessionLocal()
try:
    c = session.query(ConversationHistory).order_by(ConversationHistory.id.desc()).first()
    if c:
        print(f"ID: {c.id}")
        print(f"Timestamp: {c.timestamp}")
        print(f"Query: {c.query}")
        print(f"Intent: {c.intent}")
        print(f"Response: {c.response}")
        print(f"Context: {c.context}")
    else:
        print("No conversations found.")
finally:
    session.close()
