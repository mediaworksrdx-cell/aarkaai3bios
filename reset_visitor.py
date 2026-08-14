import sys
sys.path.insert(0, "/home/ubuntu/aarkaai3b")
from database import SessionLocal, UserAccount
from modules.auth import get_password_hash

db = SessionLocal()
user = db.query(UserAccount).filter(UserAccount.email == "visitor@aarkaai.com").first()
if user:
    user.password_hash = get_password_hash("VisitorSecurePassword123!")
    db.commit()
    print("DONE - password updated for:", user.email)
else:
    print("User not found")
db.close()
