import sys
import logging
from modules.auth import register_user

logging.basicConfig(level=logging.INFO)

try:
    print("Registering visitor@aarkaai.com...")
    res = register_user(
        email='visitor@aarkaai.com',
        password='VisitorSecurePassword123!',
        name='Web Visitor'
    )
    print("Successfully registered default visitor!")
    print(res)
except Exception as e:
    print(f"Error registering visitor: {e}")
    sys.exit(1)
