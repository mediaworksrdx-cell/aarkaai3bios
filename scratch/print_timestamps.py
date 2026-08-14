from database import SessionLocal, ConversationHistory

session = SessionLocal()
try:
    convs = session.query(ConversationHistory).order_by(ConversationHistory.id.asc()).all()
    for c in convs:
        print(f"ID: {c.id} | Timestamp: {c.timestamp} | Query: {repr(c.query)}")
finally:
    session.close()
