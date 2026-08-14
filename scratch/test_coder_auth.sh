#!/bin/bash
# Step 1: Register test user (ignore if already exists)
curl -s -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"aarka_test","password":"test123","email":"test@aarka.ai"}' | python3.13 -c "import sys,json; r=json.load(sys.stdin); print('REGISTER:', r.get('message','ok'))" 2>/dev/null

# Step 2: Login and get token
TOKEN=$(curl -s -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"aarka_test","password":"test123"}' | python3.13 -c "import sys,json; r=json.load(sys.stdin); print(r.get('access_token',''))")

echo "TOKEN: $TOKEN"

# Step 3: Send coding question
curl -s -X POST http://localhost:5000/prompt \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"message":"Write a Python Binary Search Tree class with insert, search, and inorder traversal. Add time complexity comments.","session_id":"coder-bst-test","stream":false}'
