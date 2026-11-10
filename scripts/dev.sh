#!/usr/bin/env bash
set -euo pipefail
(cd backend && uvicorn app.main:app --reload --port 8000) &
(cd frontend && npm run dev)
