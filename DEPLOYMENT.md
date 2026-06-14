# Deployment — Production Stack

```
┌─────────────────┐     HTTPS/JWT      ┌──────────────────────────────┐
│  React (Vercel) │ ─────────────────► │  Django + DRF (Railway)      │
│  VITE_API_URL   │                    │  Gunicorn web service        │
└─────────────────┘                    └──────────────┬───────────────┘
                                                      │
                    ┌─────────────────────────────────┼─────────────────────┐
                    │                                 │                     │
                    ▼                                 ▼                     ▼
           ┌────────────────┐              ┌────────────────┐   ┌────────────────┐
           │ Supabase       │              │ Upstash Redis  │   │ Celery worker  │
           │ PostgreSQL     │              │ (cache)        │   │ + beat         │
           │ DATABASE_URL   │              │ REDIS_URL      │   │ (Railway)      │
           └────────────────┘              └────────────────┘   └────────────────┘
```

## 1. Supabase (database)

1. Create project at [supabase.com](https://supabase.com)
2. **Settings → Database → Connection string** (URI mode)
3. Use the **pooler** URL (port `6543`) for Railway
4. Set on Railway:

```env
DATABASE_URL=postgresql://postgres.[ref]:[password]@....pooler.supabase.com:6543/postgres?sslmode=require
```

## 2. Upstash Redis (cache + Celery)

1. Create database at [upstash.com](https://upstash.com)
2. Copy the **Redis URL** (`rediss://` for TLS)
3. Set on Railway:

```env
REDIS_URL=rediss://default:TOKEN@HOST.upstash.io:6379
```

Same URL is used for Django cache and Celery broker. Optional overrides:

```env
CELERY_BROKER_URL=rediss://...
CELERY_RESULT_BACKEND=rediss://...
```

## 3. Railway (Django backend) — 3 services

Set **root directory** to `backend` for each service.

### Service A — Web (required)

| Setting | Value |
|---------|-------|
| Start command | `gunicorn food_ordering.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120` |
| Health check | `/health/` |
| `DJANGO_SETTINGS_MODULE` | `food_ordering.settings_production` |

Pre-deploy:

```bash
python manage.py migrate --noinput && python manage.py collectstatic --noinput && python manage.py ensure_admin_user
```

### Service B — Celery worker (required for background jobs)

| Setting | Value |
|---------|-------|
| Start command | `celery -A food_ordering worker --loglevel=info --concurrency=2` |
| Same env vars | Copy all vars from Web service |

### Service C — Celery beat (required for scheduled tasks)

| Setting | Value |
|---------|-------|
| Start command | `celery -A food_ordering beat --loglevel=info` |
| Same env vars | Copy all vars from Web service |

**Run only one beat instance** (not multiple replicas).

## 4. Vercel (React frontend)

1. Deploy React app from `frontend/` (when built)
2. Set env var:

```env
VITE_API_URL=https://your-api.up.railway.app
```

3. Add the Vercel URL to Railway backend:

```env
CORS_ALLOWED_ORIGINS=https://your-app.vercel.app
CSRF_TRUSTED_ORIGINS=https://your-app.vercel.app
```

## 5. API auth (React → Django)

React uses JWT via DRF:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/auth/login/` | POST | Get access + refresh tokens |
| `/api/auth/token/refresh/` | POST | Refresh access token |
| `/api/auth/profile/` | GET | User profile |

Send header: `Authorization: Bearer <access_token>`

## 6. Celery tasks (scheduled)

| Task | Schedule | Purpose |
|------|----------|---------|
| `generate_daily_order_reports` | Every hour | Kitchen reports |
| `finalize_daily_menu_reports` | Every 15 min | After cutoff time |
| `cleanup_cancelled_orders` | Daily 2 AM | DB cleanup |

## 7. Estimated monthly cost

| Service | Cost |
|---------|------|
| Vercel (Hobby) | $0 |
| Railway Web | ~$5–7 |
| Railway Celery worker | ~$5 |
| Railway Celery beat | ~$5 |
| Supabase (free tier) | $0 |
| Upstash (free tier) | $0 |
| **Total** | **~$15–20/month** |

## 8. Local production test

```bash
# Fill backend/.env from backend/.env.example
./start.sh prod          # Web only (Gunicorn)

# Separate terminals for Celery:
cd backend
export DJANGO_SETTINGS_MODULE=food_ordering.settings_production
celery -A food_ordering worker --loglevel=info
celery -A food_ordering beat --loglevel=info
```
