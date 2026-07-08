# Local Development Startup Guide

This guide explains how to get xend paybot running locally for development.

## Quick Start (Recommended)

```bash
bash start-dev.sh
```

This single command:
1. Checks Python and Node are installed
2. Creates a Python virtual environment (`.venv/`)
3. Installs all Python dependencies
4. Installs all frontend dependencies
5. Creates `.env` files from templates
6. Starts both backend and frontend with live-reload

The services will be available at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

Press `Ctrl+C` to stop both services.

---

## Installation-Only Setup

To prepare the environment without starting services, use the bootstrap script:

```bash
bash bootstrap.sh
```

This prepares everything but doesn't start the dev servers. Useful for CI/automation or when you want manual control.

---

## Manual Step-by-Step

### 1. Backend Setup

```bash
# Create virtual environment
cd backend
python3 -m venv .venv

# Activate (Linux/Mac)
source .venv/bin/activate

# Or on Windows:
# .venv\Scripts\activate

# Upgrade pip
python -m pip install --upgrade pip

# Install dependencies
python -m pip install -r requirements.txt
```

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies (pnpm is faster, but npm works too)
pnpm install

# Or if you prefer npm:
# npm install
```

### 3. Environment Configuration

Copy `.env` examples (or let `start-dev.sh` do this automatically):

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

For local development, these templates provide safe defaults. Update them if needed:
- `backend/.env`: Set `TELEGRAM_BOT_TOKEN`, `JWT_SECRET_KEY`, etc.
- `frontend/.env`: Set `VITE_API_BASE_URL` if needed (defaults to `/api`)

### 4. Start Services

**Backend:**
```bash
cd backend
source .venv/bin/activate
uvicorn main:app --reload --port 8000
```

**Frontend (in a new terminal):**
```bash
cd frontend
pnpm dev
```

---

## Troubleshooting

### "Python not found"
Install Python 3.11+ from https://www.python.org

### "pnpm not found"
Install pnpm with:
```bash
npm install -g pnpm
```

Or enable Corepack (Node 16.10+):
```bash
corepack enable pnpm
```

### "node_modules: Permission denied"
Clear node_modules and reinstall:
```bash
cd frontend
rm -rf node_modules pnpm-lock.yaml
pnpm install
```

### Backend won't start: "address already in use"
Port 8000 is already in use. Either:
- Kill the process: `pkill -f "uvicorn"`
- Or use a different port: `uvicorn main:app --port 8001`

### Frontend won't start: "EADDRINUSE :::5173"
Port 5173 is already in use. Let Vite pick a new port:
```bash
cd frontend
pnpm dev --port 5174
```

### Database errors
The backend uses SQLite by default (`paybot.db`). To reset:
```bash
cd backend
rm paybot.db
```

The database will be recreated on the next startup.

### "TypeError: Cannot read property 'split' of undefined"
Often caused by missing `.env` files. Run `bash start-dev.sh` to auto-create them.

---

## Running Tests

### Backend Tests

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

Or with short output format:
```bash
pytest tests/ -v --tb=short
```

### Frontend Linting

```bash
cd frontend
pnpm lint
```

### Frontend Build

```bash
cd frontend
pnpm build
```

---

## Development Workflow

### Code Changes Auto-Reload

Both services have live-reload enabled:
- **Backend**: Uvicorn watches Python files and restarts automatically
- **Frontend**: Vite hot-reloads on every change

### Running with Debugger

**Backend (Python debugger):**
```bash
cd backend
python -m debugpy --listen 5678 -m uvicorn main:app --reload --port 8000
```

Then attach your debugger to localhost:5678 (VS Code, PyCharm, etc.)

**Frontend:**
- VS Code: F5 to debug (launch config included)
- Or use DevTools (F12) in your browser

---

## Useful Environment Variables

**Backend (.env):**
- `ENVIRONMENT=development` - Enable dev-friendly validation
- `DEBUG=true` - Verbose logging
- `DATABASE_URL` - Database connection (defaults to SQLite)
- `TELEGRAM_BOT_TOKEN` - Telegram bot token (required for bot features)
- `JWT_SECRET_KEY` - Auto-generated if not set in development

**Frontend (.env):**
- `VITE_API_BASE_URL` - Backend API URL (defaults to `/api`)
- `VITE_ENVIRONMENT` - "development" or "production"

---

## Docker Development (Advanced)

To run in Docker:

```bash
# Build image
docker build -t paybot:dev .

# Run container
docker run -p 8000:8000 -p 5173:5173 \
  -e TELEGRAM_BOT_TOKEN="your_token" \
  -e JWT_SECRET_KEY="your_secret" \
  paybot:dev
```

---

## Next Steps

- Read [backend/README.md](backend/README.md) for API details
- Read [frontend/README.md](frontend/README.md) for UI component docs
- Check [DEPLOYMENT.md](backend/DEPLOYMENT.md) for production setup
