#!/bin/bash
# Add a debug print by patching the live process via a debug endpoint
cd /workspace/aarkaai3b
curl -s -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"debug_user_x9z","password":"debug_pass_x9z","email":"debug@debug.com"}' > /tmp/debug_register.json

TOKEN=$(python3.13 -c "
import json
with open('/tmp/debug_register.json') as f:
    data = json.load(f)
print(data.get('access_token', ''))
")

echo "Token: $TOKEN"

# Now call with a tiny diagnostic payload to check classify directly
python3.13 - <<'EOF'
import sys
sys.path.insert(0, '/workspace/aarkaai3b')
from modules import semantic_filter
q = "Write a Python Binary Search Tree class with insert, search, and inorder traversal. Add time complexity comments for each method."
res = semantic_filter.classify(q)
print("DEBUG classify result in RUNNING process:", res)
EOF
