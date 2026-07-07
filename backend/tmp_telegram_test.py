import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault('DISABLE_BACKGROUND_TASKS', '1')
from main import app
from fastapi.testclient import TestClient

result = {'routes': [], 'call': None, 'exception': None}
for route in app.routes:
    if hasattr(route, 'path') and '/api/v1/telegram/webhook' in route.path:
        result['routes'].append({'path': route.path, 'methods': sorted(route.methods or []), 'name': route.name})

try:
    with TestClient(app) as client:
        r = client.post('/api/v1/telegram/webhook', json={})
        result['call'] = {'status_code': r.status_code, 'json': r.json()}
except Exception as e:
    result['exception'] = str(e)

with open('tmp_telegram_test_result.json', 'w', encoding='utf-8') as f:
    import json
    json.dump(result, f, indent=2)
print('done')
