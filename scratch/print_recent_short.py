from database import SessionLocal, ConversationHistory

session = SessionLocal()
try:
    entries = session.query(ConversationHistory).order_by(ConversationHistory.id.desc()).limit(5).all()
    for c in entries:
        print(f"ID: {c.id} | Timestamp: {c.timestamp} | User: {c.user_id}")
        print(f"Query: {repr(c.query)}")
        print(f"Response: {repr(c.response)}")
        print(f"Intent: {c.intent} | Source: {c.source}")
        print("-" * 50)
finally:
    session.close()
