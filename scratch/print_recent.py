from database import SessionLocal, ConversationHistory

session = SessionLocal()
try:
    entries = session.query(ConversationHistory).order_by(ConversationHistory.id.desc()).limit(10).all()
    for c in entries:
        print(f"ID: {c.id} | Timestamp: {c.timestamp} | User: {c.user_id} | Session: {c.session_id}")
        print(f"Query: {c.query}")
        print(f"Response: {c.response}")
        print("-" * 50)
finally:
    session.close()
