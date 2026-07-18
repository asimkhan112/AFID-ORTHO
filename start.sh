#!/usr/bin/env bash
# Production start command (Railway / any container host).
#   1. Apply database migrations (idempotent — no-op if already at head).
#   2. Seed baseline data (idempotent — seed.py skips if accounts already exist).
#   3. Launch the API bound to the platform-provided $PORT.
set -e

echo "→ Running database migrations (alembic upgrade head)…"
alembic upgrade head

echo "→ Seeding baseline data (idempotent)…"
python seed.py || echo "  (seed skipped or already present)"

echo "→ Starting API on port ${PORT:-8000}…"
exec uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
