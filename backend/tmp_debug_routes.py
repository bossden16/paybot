from pathlib import Path
import os
import json
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault('DISABLE_BACKGROUND_TASKS', '1')
from main import app
routes = []
for route in app.routes:
    routes.append({
        'path': route.path,
        'methods': sorted(route.methods or []),
        'name': route.name,
        'endpoint': getattr(route.endpoint, '__name__', str(route.endpoint)),
    })
with open('route_info.json', 'w', encoding='utf-8') as f:
    json.dump(routes, f, indent=2)
print('wrote route_info.json')
