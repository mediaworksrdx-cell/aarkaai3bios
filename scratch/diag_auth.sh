#!/bin/bash
echo "=== REGISTER ==="
curl -s -X POST http://localhost:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"codertest","password":"Coder@123","email":"coder@aarka.ai"}'

echo ""
echo "=== LOGIN ==="
curl -s -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"codertest","password":"Coder@123"}'
