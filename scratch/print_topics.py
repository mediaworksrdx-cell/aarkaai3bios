from database import SessionLocal, KnowledgeEntry
session = SessionLocal()
entries = session.query(KnowledgeEntry).all()
for e in entries:
    print(e.topic)
session.close()
