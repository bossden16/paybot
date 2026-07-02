# Contributing to xend Philippines

Thank you for contributing! This guide summarizes the repository conventions, local development workflow, and recommended practices.

## Developer workflow

### 1. Setup your local environment
- Install Python 3.11.
- Install Node.js LTS.
- Ensure `git` is available.
- On Linux/macOS, use the included startup script:
  - `bash start_app_v2.sh`

### 2. Environment variables
- Copy the example files:
  - `cp backend/.env.example backend/.env`
  - `cp frontend/.env.example frontend/.env`
- Populate required secrets and URLs.
- Use `.env` files only for local development.

### 3. Install dependencies
- Backend:
  - `cd backend`
  - `python -m pip install --upgrade pip`
  - `python -m pip install -r requirements.txt`
- Frontend:
  - `cd frontend`
  - `pnpm install`

### 4. Start services
- Linux/macOS:
  - `bash start_app_v2.sh`
- Windows:
  - `.\setup_windows.ps1`
  - `.\start_local_windows.ps1`

### 5. Run tests and linting
- Backend tests:
  - `cd backend && python -m pytest tests/ -v --tb=short`
- Frontend lint:
  - `cd frontend && pnpm lint`

### 6. Build for production
- Frontend build:
  - `cd frontend && pnpm build`
- Backend run command for local production-style startup:
  - `cd backend && uvicorn main:app --host 0.0.0.0 --port 8000`

### 7. Branching and PRs
- Develop in feature branches.
- Keep `main` clean and stable.
- Use descriptive branch names like `feature/add-wallet-logging` or `fix/telegram-auth`.
- Open pull requests against `main` with a summary and testing notes.

## Notes for contributors

- Use `backend/.env.example` and `frontend/.env.example` as templates.
- Do not commit secrets or API keys.
- If you change frontend assets, verify the built output and static asset path if the backend serves files from `backend/static/`.
- Keep backend service methods `async` and return standard JSON structures where applicable.

## Helpful documents
- `backend/README.md` — backend architecture and deployment notes.
- `frontend/README.md` — frontend stack and basic commands.
- `docs/API_DOCUMENTATION_GUIDE.md` — API and integration reference.
- `PRODUCTION_CHECKLIST.md` — production readiness and security checks.
