from database import SessionLocal, ConversationHistory, PersonalChat, RLHFFeedback

session = SessionLocal()
try:
    print("Clearing ConversationHistory...")
    deleted_convs = session.query(ConversationHistory).delete()
    print("Clearing PersonalChat...")
    deleted_chats = session.query(PersonalChat).delete()
    print("Clearing RLHFFeedback...")
    deleted_rlhf = session.query(RLHFFeedback).delete()
    session.commit()
    print(f"Successfully cleared:\n- {deleted_convs} conversation history entries\n- {deleted_chats} personal chat entries\n- {deleted_rlhf} RLHF feedback entries.")
except Exception as e:
    session.rollback()
    print("Error clearing tables:", e)
finally:
    session.close()
