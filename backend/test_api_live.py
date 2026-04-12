import sys, json, urllib.request, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'backend')

def api_get(path):
    req = urllib.request.Request(f'http://localhost:8000{path}', headers={'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=5) as resp:
        return json.loads(resp.read())

tests = [
    ('/api/products',           lambda d: len(d.get('products',[])) > 0),
    ('/api/search?q=green+mat', lambda d: len(d.get('products',[])) > 0),
    ('/api/ml/insights',        lambda d: 'model_status' in d),
    ('/api/metrics',            lambda d: 'p99Latency' in d),
]

passed = 0
for path, check in tests:
    try:
        data = api_get(path)
        if check(data):
            print(f'  [PASS]  GET {path}')
            passed += 1
        else:
            print(f'  [FAIL]  GET {path}  check failed. keys={list(data.keys())}')
    except Exception as e:
        print(f'  [FAIL]  GET {path}  {e}')

# Semantic search detail
try:
    data = api_get('/api/search?q=green+mat')
    parsed = data.get('query_parsed', {})
    top = data['products'][0]['name'] if data.get('products') else ''
    print(f'  [INFO]  Color parsed: {parsed.get("colors")}')
    print(f'  [INFO]  Top result: {top}')
    print(f'  [INFO]  Yoga ranked #1: {"Yoga" in top}')
    print(f'  [INFO]  model_status: {api_get("/api/ml/insights").get("model_status")}')
except Exception as e:
    print(f'  [FAIL]  search detail: {e}')

print(f'\n  Live API: {passed}/{len(tests)} passed')
