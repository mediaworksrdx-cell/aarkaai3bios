#!/bin/bash
# Register gets us the token directly
RESPONSE=$(curl -s -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"bsttest_'$RANDOM'","password":"Coder@123","email":"bst'$RANDOM'@aarka.ai"}')

TOKEN=$(echo $RESPONSE | python3.13 -c "import sys,json; r=json.load(sys.stdin); print(r.get('access_token',''))")
echo "Token obtained: ${TOKEN:0:40}..."

echo ""
echo "=== SENDING CODING QUESTION TO AARKA CODER 3B ==="
echo ""

START=$(date +%s%3N)
RESULT=$(curl -s -X POST http://localhost:5000/prompt \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "Write a Python Binary Search Tree class with insert, search, and inorder traversal. Add time complexity comments for each method.",
    "session_id": "coder-bst-live",
    "mode": "production"
  }')
END=$(date +%s%3N)
ELAPSED=$(( (END - START) ))

echo "Time: ${ELAPSED}ms"
echo ""
echo "$RESULT" | python3.13 -c "
import sys, json
r = json.load(sys.stdin)
print('Model   :', r.get('model', 'N/A'))
print('Domain  :', r.get('domain', r.get('intent', 'N/A')))
print('Tokens  :', r.get('usage', {}))
print()
print('--- RESPONSE ---')
print(r.get('response', r.get('content', json.dumps(r, indent=2))))
"
