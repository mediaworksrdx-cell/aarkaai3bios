from database import SessionLocal, KnowledgeEntry
session = SessionLocal()
entries = session.query(KnowledgeEntry).filter(KnowledgeEntry.topic.like('RLHF Correction for User%')).all()
for entry in entries:
    if 'Conv' in entry.topic:
        conv_part = entry.topic.split('(')[1].split(')')[0]
        entry.topic = f'Global System Correction (RLHF) ({conv_part})'
    else:
        entry.topic = 'Global System Correction (RLHF)'
session.commit()
print(f'Updated {len(entries)} entries.')
session.close()
