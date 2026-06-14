#!/usr/bin/env bash
# Food Ordering Platform — local dev or production startup
#
# Usage:
#   ./start.sh          # local development (SQLite, runserver)
#   ./start.sh dev      # same as above
#   ./start.sh prod     # production (PostgreSQL, gunicorn, collectstatic)
#
# Production requires backend/.env with at least:
#   SECRET_KEY=...
#   DATABASE_URL=postgresql://...
#   ALLOWED_HOSTS=your-app.up.railway.app
#   DEBUG=False

set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
VENV_PYTHON="$BACKEND/venv/bin/python"
ENV_FILE="$BACKEND/.env"
MODE="${1:-dev}"
PORT="${PORT:-8000}"
WEB_CONCURRENCY="${WEB_CONCURRENCY:-}"

load_env() {
  if [ -f "$ENV_FILE" ]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
  fi
}

ensure_venv() {
  cd "$BACKEND"
  if [ ! -x "$VENV_PYTHON" ]; then
    echo "==> Creating virtual environment..."
    python3 -m venv venv
    "$VENV_PYTHON" -m pip install -q -r requirements.txt
    "$VENV_PYTHON" -m pip install -q setuptools
  fi
}

run_migrations() {
  echo "==> Running migrations..."
  "$VENV_PYTHON" manage.py migrate --settings="$SETTINGS" --noinput
}

ensure_admin() {
  echo "==> Ensuring standard admin account..."
  "$VENV_PYTHON" manage.py ensure_admin_user --settings="$SETTINGS"
}

ensure_demo_user() {
  echo "==> Ensuring demo user account..."
  "$VENV_PYTHON" manage.py shell --settings="$SETTINGS" <<'PY'
from django.conf import settings
from apps.users.models import User, UserProfile

if not User.objects.filter(email='john@company.com').exists():
    user = User.objects.create_user(
        email='john@company.com',
        employee_id='EMP001',
        first_name='John',
        last_name='Doe',
        password='user123',
        role='user',
    )
    UserProfile.objects.create(user=user)
    print('Created demo user: john@company.com / user123')
else:
    print('Demo user ready: john@company.com / user123')

print(f"Admin login: {settings.ADMIN_EMAIL} / admin123")
PY
}

collect_static() {
  echo "==> Collecting static files..."
  "$VENV_PYTHON" manage.py collectstatic --settings="$SETTINGS" --noinput
}

stop_port_if_busy() {
  if lsof -ti:"$PORT" >/dev/null 2>&1; then
    echo "==> Stopping existing process on port $PORT..."
    lsof -ti:"$PORT" | xargs kill -15 2>/dev/null || true
    sleep 1
    if lsof -ti:"$PORT" >/dev/null 2>&1; then
      lsof -ti:"$PORT" | xargs kill -9 2>/dev/null || true
      sleep 1
    fi
  fi
}

worker_count() {
  if [ -n "$WEB_CONCURRENCY" ]; then
    echo "$WEB_CONCURRENCY"
    return
  fi
  "$VENV_PYTHON" - <<'PY'
import os
print(max(2, (os.cpu_count() or 1) * 2 + 1))
PY
}

validate_prod_env() {
  local missing=0
  for var in SECRET_KEY DATABASE_URL ALLOWED_HOSTS; do
    if [ -z "${!var:-}" ]; then
      echo "ERROR: $var is required for production. Set it in backend/.env"
      missing=1
    fi
  done
  if [ "$missing" -ne 0 ]; then
    exit 1
  fi
  if [ "${DEBUG:-False}" = "True" ] || [ "${DEBUG:-false}" = "true" ]; then
    echo "WARNING: DEBUG is enabled in production settings."
  fi
}

print_banner() {
  local mode_label="$1"
  echo ""
  echo "=============================================="
  echo "  Food Ordering Platform — $mode_label"
  echo "=============================================="
  echo "  App:        http://localhost:$PORT/"
  echo "  Health:     http://localhost:$PORT/health/"
  echo "  User menu:  http://localhost:$PORT/today-menu/"
  echo "  Admin:      http://localhost:$PORT/manage/"
  if [ "$MODE" = "dev" ]; then
    echo ""
    echo "  Admin:  ${ADMIN_EMAIL:-admin@foodordering.com} / admin123"
    echo "  User:   john@company.com / user123"
  fi
  echo "=============================================="
  echo ""
}

start_dev() {
  SETTINGS="food_ordering.settings_local"
  export DJANGO_SETTINGS_MODULE="$SETTINGS"

  ensure_venv
  load_env
  run_migrations
  ensure_admin
  ensure_demo_user
  stop_port_if_busy
  print_banner "development"

  exec "$VENV_PYTHON" manage.py runserver --settings="$SETTINGS" "0.0.0.0:$PORT"
}

start_prod() {
  SETTINGS="food_ordering.settings_production"
  export DJANGO_SETTINGS_MODULE="$SETTINGS"

  ensure_venv
  load_env
  validate_prod_env
  run_migrations
  ensure_admin
  collect_static
  stop_port_if_busy
  print_banner "production"

  WORKERS="$(worker_count)"
  echo "==> Starting Gunicorn ($WORKERS workers) on port $PORT..."
  exec "$VENV_PYTHON" -m gunicorn food_ordering.wsgi:application \
    --bind "0.0.0.0:$PORT" \
    --workers "$WORKERS" \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
}

case "$MODE" in
  dev|development|local)
    start_dev
    ;;
  prod|production)
    start_prod
    ;;
  *)
    echo "Unknown mode: $MODE"
    echo "Usage: ./start.sh [dev|prod]"
    exit 1
    ;;
esac
