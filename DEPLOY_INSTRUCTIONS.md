# Deployment Instructions and Next Steps

This repository now targets **Render** for production deployment. Render uses `render.yaml` at the repo root to define the backend service, managed database, and migration job.

## Render deployment (recommended)
1. Add the repository to Render and connect it to GitHub.
2. Confirm Render is using the `main` branch and the `backend/Dockerfile` path.
3. Use `render.yaml` to define:
   - `paybot-backend` web service on Docker
   - a managed Postgres database
   - a `migrate-database` job that runs `alembic -c backend/alembic.ini upgrade head`
4. Configure the required environment variables in the Render service settings.
5. Push your changes to `main`; Render auto-deploys from the connected repo and branch.

## Local development
Use the existing local dev scripts and startup flow instead of production deployment helpers.

## Why I couldn't deploy automatically from here
- Deployment requires private secrets and authenticated provider access. I don't have those credentials from this environment.

## Options I can do next (choose one)
- I can create a GitHub Issue template with the Render environment checklist so collaborators can fill it in.
- I can prepare a PR containing the Render deployment docs and cleanup changes.
- If you provide temporary credentials (not recommended), I can attempt a deploy from this environment.
- Or you can connect Render to the repo and trigger its auto-deploy; I can then monitor the run if you give me the run URL.

