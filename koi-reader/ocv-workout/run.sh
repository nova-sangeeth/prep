#!/usr/bin/env bash
#
# run.sh — one entry point for the whole OCV Workout project.
#
# Usage:
#   ./run.sh setup            create venv + install requirements
#   ./run.sh stage1           webcam shape counter
#   ./run.sh stage2           color detect + track + classify
#   ./run.sh api              start the FastAPI detection server
#   ./run.sh client <img> [n] hit the API (n concurrent, default 1)
#   ./run.sh redis            start a local Redis in Docker
#
set -euo pipefail

# Resolve project dir so the script works from anywhere.
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

VENV="$ROOT/env"
PY="$VENV/bin/python"

ensure_venv() {
  if [[ ! -x "$PY" ]]; then
    echo "No venv found. Run: ./run.sh setup" >&2
    exit 1
  fi
}

cmd="${1:-help}"
shift || true

case "$cmd" in
  setup)
    echo "==> Creating venv at $VENV"
    python3 -m env "$VENV"
    echo "==> Installing requirements"
    "$PY" -m pip install --upgrade pip
    "$PY" -m pip install -r requirements.txt
    echo "==> Done. Try: ./run.sh stage1"
    ;;

  stage1)
    ensure_venv
    exec "$PY" stage1_shape_counter.py
    ;;

  stage2)
    ensure_venv
    exec "$PY" stage2_tracker.py
    ;;

  api)
    ensure_venv
    # --reload for dev convenience; drop it for a throughput test.
    exec "$VENV/bin/uvicorn" api:app --host 0.0.0.0 --port 8000 --reload
    ;;

  client)
    ensure_venv
    if [[ $# -lt 1 ]]; then
      echo "usage: ./run.sh client <image> [n]" >&2
      exit 1
    fi
    exec "$PY" client.py "$@"
    ;;

  redis)
    echo "==> Starting Redis on :6379 (Ctrl-C to stop)"
    exec docker run --rm -p 6379:6379 redis
    ;;

  help|*)
    sed -n '3,14p' "$ROOT/run.sh"
    ;;
esac
