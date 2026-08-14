from database import SessionLocal, ConversationHistory
from modules.aarkaa_engine import _clean_response

session = SessionLocal()
try:
    c = session.query(ConversationHistory).filter(ConversationHistory.id == 20).first()
    if c:
        text = c.response
        print(f"Original response length: {len(text)}")
        print(f"Original ends with: {repr(text[-50:])}")
        
        # Test clean response
        cleaned = _clean_response(text)
        print(f"Cleaned response length: {len(cleaned)}")
        print(f"Cleaned ends with: {repr(cleaned[-50:])}")
finally:
    session.close()
