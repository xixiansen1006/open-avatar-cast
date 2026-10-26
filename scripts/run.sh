#!/usr/bin/env bash
# 启动 open-avatar-cast
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ -f .venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv/bin/activate
fi

export PYTHONPATH="${ROOT}${PYTHONPATH:+:$PYTHONPATH}"

HOST="${OAC_HOST:-0.0.0.0}"
PORT="${OAC_PORT:-8765}"

echo "[open-avatar-cast] http://${HOST}:${PORT}/"
exec python -m uvicorn backend.main:app --host "$HOST" --port "$PORT"
