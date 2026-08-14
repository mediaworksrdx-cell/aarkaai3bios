#!/bin/bash
curl -s http://localhost:5000/openapi.json | python3.13 -c "
import sys, json
d = json.load(sys.stdin)
for p in d.get('paths', {}).keys():
    print(p)
"
