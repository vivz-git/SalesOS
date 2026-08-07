# SalesOS

Production monorepo scaffold for SalesOS.

## Applications

- `frontend/` — Next.js 15 product client, deployed to Vercel.
- `backend/` — FastAPI control-plane scaffold, deployed to Railway.

## Local development

1. Copy `.env.example` into local environment files as needed.
2. Install frontend dependencies with `pnpm install`.
3. Install backend dependencies with `uv sync --all-groups` from `backend/`.
4. Run `pnpm dev` for the frontend and `uv run fastapi dev app/main.py` from `backend/` for the API.

The only implemented API route is `GET /health`. Product features belong to future, documented work.
