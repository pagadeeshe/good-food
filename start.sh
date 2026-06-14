#!/usr/bin/env bash
# Good Food — run backend + frontend locally with one command
#
# Usage:
#   ./start.sh          # API (:8000) + React (:5173)
#   ./start.sh api      # API only
#   ./start.sh frontend # React only

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
VENV="$BACKEND/venv"
PYTHON="$VENV/bin/python"
MODE="${1:-all}"

stop_port() {
  local port="$1"
  if lsof -ti:"$port" >/dev/null 2>&1; then
    echo "==> Stopping process on port $port..."
    lsof -ti:"$port" | xargs kill -15 2>/dev/null || true
    sleep 1
    lsof -ti:"$port" | xargs kill -9 2>/dev/null || true
  fi
}

ensure_backend() {
  cd "$BACKEND"
  if [ ! -x "$PYTHON" ]; then
    echo "==> Creating Python virtual environment..."
    python3 -m venv venv
  fi
  echo "==> Installing Python dependencies..."
  "$PYTHON" -m pip install -q --upgrade pip setuptools wheel
  "$PYTHON" -m pip install -q -r requirements.txt

  export DJANGO_SETTINGS_MODULE=food_ordering.settings_local
  echo "==> Running migrations..."
  "$PYTHON" manage.py migrate --noinput
  echo "==> Ensuring admin account..."
  "$PYTHON" manage.py ensure_admin_user
}

ensure_frontend() {
  cd "$FRONTEND"
  if [ ! -d node_modules ]; then
    echo "==> Installing frontend dependencies..."
    npm install
  fi
}

start_api() {
  stop_port 8000
  cd "$BACKEND"
  export DJANGO_SETTINGS_MODULE=food_ordering.settings_local
  echo "==> Starting API on http://localhost:8000"
  "$PYTHON" manage.py runserver 0.0.0.0:8000 &
  API_PID=$!
}

start_ui() {
  stop_port 5173
  cd "$FRONTEND"
  echo "==> Starting frontend on http://localhost:5173"
  npm run dev &
  UI_PID=$!
}

print_banner() {
  echo ""
  echo "=============================================="
  echo "  Good Food — local development"
  echo "=============================================="
  echo "  App:    http://localhost:5173"
  echo "  API:    http://localhost:8000"
  echo "  Admin:  http://localhost:8000/django-admin/"
  echo ""
  echo "  Login:  admin@foodordering.com / admin123"
  echo "=============================================="
  echo "  Press Ctrl+C to stop"
  echo ""
}

cleanup() {
  echo ""
  echo "==> Shutting down..."
  [ -n "${API_PID:-}" ] && kill "$API_PID" 2>/dev/null || true
  [ -n "${UI_PID:-}" ] && kill "$UI_PID" 2>/dev/null || true
  stop_port 8000
  stop_port 5173
  exit 0
}

run_all() {
  ensure_backend
  ensure_frontend
  start_api
  start_ui
  print_banner
  trap cleanup INT TERM
  wait
}

run_api_only() {
  ensure_backend
  export DJANGO_SETTINGS_MODULE=food_ordering.settings_local
  stop_port 8000
  echo "==> API: http://localhost:8000"
  cd "$BACKEND"
  exec "$PYTHON" manage.py runserver 0.0.0.0:8000
}

run_frontend_only() {
  ensure_frontend
  stop_port 5173
  echo "==> App: http://localhost:5173"
  cd "$FRONTEND"
  exec npm run dev
}

case "$MODE" in
  all|dev|start|"")
    run_all
    ;;
  api|backend)
    run_api_only
    ;;
  frontend|ui)
    run_frontend_only
    ;;
  *)
    echo "Usage: ./start.sh [all|api|frontend]"
    exit 1
    ;;
esac
