import requests

BASE = 'https://synthetixanalytics.com'

print("Running Post-Deployment Checks...")
print("-" * 40)

# 1. Health check
try:
    r = requests.get(f'{BASE}/health', timeout=10)
    print(f'Health: {r.status_code} {r.json()}')
except Exception as e:
    print(f'Health check failed: {e}')

# 2. Verify security headers
try:
    r = requests.get(f'{BASE}/', timeout=10)
    for h in ['Strict-Transport-Security', 'X-Content-Type-Options', 'X-Frame-Options']:
        print(f'{h}: {r.headers.get(h, "MISSING")}')
except Exception as e:
    print(f'Security headers check failed: {e}')

# 3. Verify admin endpoints require auth
for endpoint in ['/admin/stats', '/metrics', '/subscription/upgrade']:
    try:
        r = requests.get(f'{BASE}{endpoint}', timeout=10)
        print(f'{endpoint}: {r.status_code} (expect 401/403)')
    except Exception as e:
        print(f'{endpoint} check failed: {e}')

# 4. Verify SSE streaming endpoint is proxied
try:
    r = requests.options(f'{BASE}/prompt/stream', timeout=10)
    print(f'/prompt/stream reachable: {r.status_code}')
except Exception as e:
    print(f'/prompt/stream check failed: {e}')

print("-" * 40)
print("Checks complete.")
