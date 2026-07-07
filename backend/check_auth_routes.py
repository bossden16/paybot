from main import app
from fastapi.testclient import TestClient
import os

os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:///./tmp_auth_test.db')
os.environ.setdefault('JWT_SECRET_KEY', 'test')
os.environ.setdefault('TELEGRAM_BOT_TOKEN', '123456:TEST')
os.environ.setdefault('TELEGRAM_ADMIN_IDS', '123456')

c = TestClient(app)

print('Registered auth routes:')
for r in app.routes:
    path = getattr(r, 'path', None)
    if path and '/api/v1/auth' in path:
        print('-', path, getattr(r, 'methods', None))

print('\nEndpoint checks:')
res_get = c.get('/api/v1/auth/login')
print('GET /api/v1/auth/login ->', res_get.status_code)
print('  Location:', res_get.headers.get('location'))
res_post = c.post('/api/v1/auth/login', json={'email':'admin@paybot.local','password':'admin123'})
print('POST /api/v1/auth/login ->', res_post.status_code)
print('  Body:', res_post.text[:200])
