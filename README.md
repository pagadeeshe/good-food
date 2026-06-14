# Food Ordering Platform

A scalable food ordering platform supporting 10,000+ users with daily menu management and real-time order processing.

## Architecture

```
Frontend (React + TypeScript)
    ↓
Backend API (Django + DRF)
    ↓
Database (PostgreSQL/Supabase) + Cache (Redis)
```

## Features

- **Admin Portal**: Menu management, order analytics, user management
- **User Portal**: Daily menu viewing, order placement, monthly summaries
- **Scalability**: Supports 10,000+ users and 2,000+ concurrent users
- **Security**: JWT authentication, rate limiting, CSRF protection
- **Performance**: Redis caching, optimized database queries

## Tech Stack

### Backend
- Django 4.x
- Django REST Framework
- JWT Authentication
- PostgreSQL (Supabase)
- Redis
- Celery

### Frontend
- React 19
- TypeScript
- Vite
- Material UI
- React Query
- React Router

## Quick Start

### Backend Setup
```bash
cd backend
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### Redis Setup
```bash
redis-server
```

## API Endpoints

### Authentication
- POST `/api/auth/login` - User login
- POST `/api/auth/logout` - User logout  
- GET `/api/auth/profile` - Get user profile

### User APIs
- GET `/api/menu/today` - Get today's menu
- POST `/api/orders` - Place order
- GET `/api/orders/history` - Order history
- GET `/api/orders/monthly-summary` - Monthly summary

### Admin APIs
- POST `/api/admin/menu` - Create menu
- GET `/api/admin/reports/daily` - Daily reports
- GET `/api/admin/users` - Manage users

## Database Models

- **User**: Employee information and authentication
- **WeeklyMenu**: Weekly menu planning
- **DailyMenu**: Daily menu with cutoff times
- **MenuItem**: Individual food items
- **Order**: User orders
- **OrderItem**: Order line items

## Security Features

- JWT token authentication (15min access, 7 day refresh)
- Role-based permissions (Admin/User)
- Rate limiting (Redis-based)
- CSRF protection
- HTTPS enforcement
- Password hashing (bcrypt)

## Performance Optimizations

- Redis caching for menus and summaries
- Database query optimization
- Background job processing with Celery
- Load balancer ready architecture

## Deployment

Recommended stack:
- **Frontend**: Vercel
- **Backend**: Docker containers
- **Database**: Supabase PostgreSQL
- **Cache**: Redis Cloud
- **Monitoring**: Sentry + Prometheus

## License

MIT License