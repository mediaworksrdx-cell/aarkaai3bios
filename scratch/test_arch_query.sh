#!/bin/bash
# Test that architecture/design queries go through LLM, not execution_engine
RESPONSE=$(curl -s -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"archtest_'$RANDOM'","password":"Arch@123","email":"arch'$RANDOM'@aarka.ai"}')

TOKEN=$(echo $RESPONSE | python3.13 -c "import sys,json; r=json.load(sys.stdin); print(r.get('access_token',''))")
echo "Token: ${TOKEN:0:30}..."

echo ""
echo "=== ARCHITECTURE DESIGN QUERY TEST ==="
echo ""

START=$(date +%s%3N)
RESULT=$(curl -s -X POST http://localhost:5000/prompt \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "Design a production-grade distributed code execution platform that can safely run untrusted Python, Java, C++, and JavaScript code for 1 million users. Provide architecture, APIs, database schema, sandboxing, scheduling, scaling, failure recovery, and security. Explain all trade-offs",
    "session_id": "arch-design-test-1",
    "mode": "production"
  }')
END=$(date +%s%3N)
ELAPSED=$(( (END - START) ))

echo "Time: ${ELAPSED}ms"
echo ""
echo "$RESULT" | python3.13 -c "
import sys, json
r = json.load(sys.stdin)
print('Domain  :', r.get('domain', r.get('intent', 'N/A')))
print()
resp = r.get('response', r.get('content', json.dumps(r, indent=2)))
# Print first 1500 chars
print('--- RESPONSE (first 1500 chars) ---')
print(resp[:1500])
print()
print('--- RESPONSE LENGTH ---')
print(len(resp), 'chars')
"
