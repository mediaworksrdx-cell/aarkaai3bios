from database import SessionLocal, ConversationHistory

session = SessionLocal()
try:
    c = session.query(ConversationHistory).filter(ConversationHistory.id == 20).first()
    if c:
        text = c.response
        print("Tail of response:")
        print(text[-200:])
        print("\nEnds with:")
        for char in text[-50:]:
            print(f"{repr(char)}: {ord(char)}")
finally:
    session.close()
