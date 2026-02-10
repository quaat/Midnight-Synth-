#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

( cd "$ROOT/backend" && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload ) &
BACK_PID=$!
( cd "$ROOT/frontend" && npm install && NEXT_PUBLIC_SYNTH_URL=http://localhost:8000 npm run dev ) &
FRONT_PID=$!

trap 'kill $BACK_PID $FRONT_PID' INT TERM
wait
