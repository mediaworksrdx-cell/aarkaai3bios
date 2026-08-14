import os
import sys
import logging
from modules.auth import register_user

logging.basicConfig(level=logging.INFO)

visitor_email = os.getenv("VISITOR_EMAIL", "visitor@aarkaai.com")
visitor_password = os.environ["VISITOR_PASSWORD"]  # Must be set via env var — no hardcoded default

try:
    print(f"Registering {visitor_email}...")
    res = register_user(
        email=visitor_email,
        password=visitor_password,
        name='Web Visitor'
    )
    print("Successfully registered default visitor!")
    print(res)
except Exception as e:
    print(f"Error registering visitor: {e}")
    sys.exit(1)
