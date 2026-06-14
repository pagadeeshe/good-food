# Good Food

Office lunch ordering — React frontend on Vercel, Django API on Railway, PostgreSQL on Supabase.

## Repository

```
frontend/   React + TypeScript (Vercel)
backend/    Django REST API (Railway)
```

## Deploy

### Backend (Railway)

- Root directory: `backend`
- Health check: `/health/`
- On deploy: migrations, collectstatic, `ensure_admin_user`

| Variable | Required | Example |
|----------|----------|---------|
| `DJANGO_SETTINGS_MODULE` | Yes | `food_ordering.settings_production` |
| `SECRET_KEY` | Yes | long random string |
| `DEBUG` | Yes | `False` |
| `ALLOWED_HOSTS` | Yes | `your-api.up.railway.app` |
| `DATABASE_URL` | Yes | Supabase PostgreSQL connection string |
| `ADMIN_EMAIL` | Yes | `admin@yourcompany.com` |
| `CORS_ALLOWED_ORIGINS` | Yes | `https://your-app.vercel.app` |
| `REDIS_URL` | No | Upstash Redis (cache + Celery) |
| `SENTRY_DSN` | No | Sentry error tracking |

Default admin is created on deploy (`ensure_admin_user`). Change the password after first login.

### Frontend (Vercel)

- Root directory: `frontend`
- Build: `npm run build`
- Output: `dist`

| Variable | Required | Example |
|----------|----------|---------|
| `VITE_API_URL` | Yes | `https://your-api.up.railway.app` |

### Users

Add students via Django admin (`/django-admin/`) or `POST /api/users/` (admin JWT). Local and production databases are separate.

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/auth/login/` | JWT login |
| GET/POST | `/api/orders/today/` | View / place today's order |
| GET | `/api/orders/my/` | Order history |
| GET | `/api/admin/dashboard/` | Admin dashboard |
| GET | `/api/orders/reports/today/` | Kitchen report |
