# Food Ordering Platform - Setup Guide

## Project Overview

I've built a comprehensive, scalable food ordering platform designed to handle 10,000+ users and 2,000+ concurrent users. The platform includes:

### Backend Architecture (Django + DRF)
- **User Management**: Custom user model with role-based permissions (Admin/User)
- **Menu Management**: Daily menus, weekly menu templates, menu items with categories
- **Order System**: Real-time order processing with statistics and validation
- **Authentication**: JWT-based authentication with rate limiting
- **Reports & Analytics**: Pre-computed summaries and kitchen reports
- **Caching**: Redis-based caching for high-performance operations
- **Background Tasks**: Celery for asynchronous processing
- **API Documentation**: Auto-generated with DRF Spectacular

### Key Features Implemented

#### 🔐 Authentication & Security
- JWT authentication with 15-minute access tokens and 7-day refresh tokens
- Role-based permissions (Admin/User)
- Rate limiting on login attempts (5/min per IP)
- CSRF protection and secure headers
- Password hashing with bcrypt

#### 👥 User Management (Admin)
- User CRUD operations with search and filtering
- Bulk user actions (activate/deactivate, promote/demote)
- User analytics and statistics
- Inactive user identification
- Top users by order count

#### 🍽️ Menu Management
- Daily menu creation and publishing
- Weekly menu templates for recurring patterns
- Menu item management with categories and availability
- Bulk operations on menu items
- Menu statistics and popularity tracking

#### 📋 Order Processing
- Real-time order placement with validation
- Order modification before cutoff time
- Order history and monthly summaries
- Kitchen preparation reports
- Order statistics and analytics

#### 📊 Reports & Analytics
- Daily order reports for kitchen staff
- Monthly user summaries with item breakdown
- User analytics (order patterns, favorite items)
- Menu popularity statistics
- Admin dashboard metrics

#### ⚡ Performance & Scalability
- Redis caching for frequently accessed data (today's menu, user profiles)
- Database indexing for optimal query performance
- Celery background tasks for heavy operations
- Connection pooling and query optimization
- Denormalized fields for fast reads

## Database Schema

### Core Models
1. **User** - Custom user model with employee ID and roles
2. **UserProfile** - Extended user information and preferences
3. **WeeklyMenu** - Template for weekly menu planning
4. **DailyMenu** - Daily menu with status and cutoff times
5. **MenuItem** - Individual food items with categories
6. **MenuTemplate** - Reusable menu templates
7. **Order** - User orders with status tracking
8. **OrderItem** - Individual items within orders
9. **OrderSummary** - Pre-computed monthly summaries
10. **DailyOrderReport** - Kitchen preparation reports

### Key Relationships
- User ↔ Orders (One-to-Many)
- DailyMenu ↔ MenuItems (One-to-Many)
- Order ↔ OrderItems (One-to-Many)
- WeeklyMenu ↔ DailyMenus (One-to-Many)

## API Endpoints

### Authentication
- `POST /api/auth/login/` - User login with JWT
- `POST /api/auth/logout/` - Logout and blacklist token
- `POST /api/auth/register/` - User registration
- `GET /api/auth/profile/` - Get user profile
- `POST /api/auth/token/refresh/` - Refresh access token

### User Management (Admin)
- `GET /api/users/` - List all users with search/filter
- `POST /api/users/` - Create new user
- `GET /api/users/{id}/` - Get user details
- `PUT /api/users/{id}/` - Update user
- `POST /api/users/bulk-action/` - Bulk user operations

### Menu Management
- `GET /api/menu/today/` - Get today's menu (cached)
- `GET /api/menu/daily/` - List daily menus
- `POST /api/menu/daily/` - Create daily menu
- `GET /api/menu/templates/` - List menu templates
- `POST /api/menu/from-template/` - Create menu from template

### Order Management
- `POST /api/orders/` - Place new order
- `GET /api/orders/` - Get user's orders
- `PUT /api/orders/{id}/` - Modify order
- `GET /api/orders/monthly-summary/` - Monthly summary

### Reports & Analytics (Admin)
- `GET /api/reports/daily/{date}/` - Daily order report
- `GET /api/reports/monthly/{year}/{month}/` - Monthly report
- `GET /api/users/statistics/` - User statistics
- `GET /api/menu/statistics/` - Menu statistics

## Performance Features

### Caching Strategy
- **Today's Menu**: 5-minute TTL, most frequently accessed
- **User Profiles**: 5-minute TTL for authenticated users
- **Monthly Summaries**: 1-hour TTL for heavy computations
- **Statistics**: 10-15 minute TTL for admin dashboards

### Background Tasks
- **Order Statistics**: Update denormalized fields asynchronously
- **Daily Reports**: Generate kitchen reports after cutoff time
- **Monthly Summaries**: Pre-compute user summaries monthly
- **Analytics**: Update user analytics and menu statistics
- **Cleanup**: Remove old cancelled orders and logs

### Database Optimizations
- Strategic indexing on frequently queried fields
- Select_related and prefetch_related for joins
- Denormalized fields for fast reads (total_orders, total_items)
- Bulk operations for better performance

## Deployment Architecture

### Recommended Stack
```
Frontend: React + TypeScript (Vercel)
Backend: Django + DRF (Docker containers)
Database: Supabase PostgreSQL
Cache: Redis Cloud
Background Jobs: Celery + Redis
Monitoring: Sentry + Prometheus
CDN: Cloudflare
```

### Scaling Strategy
```
Load Balancer (Nginx)
    ↓
Django Instances (3+ containers)
    ↓
Database (PostgreSQL with read replicas)
    ↓
Cache Layer (Redis Cluster)
    ↓
Background Workers (Celery)
```

## Security Features

### Authentication Security
- JWT tokens with short expiration
- Refresh token rotation
- Rate limiting on auth endpoints
- Account lockout after failed attempts

### API Security
- CORS properly configured
- CSRF protection enabled
- SQL injection protection (Django ORM)
- XSS protection headers
- HTTPS enforcement in production

### Data Protection
- Sensitive data encryption
- Audit logging for admin actions
- Input validation and sanitization
- Role-based access control

## Installation & Setup

### Prerequisites
```bash
Python 3.12+
Redis Server
PostgreSQL (or use Supabase)
Node.js 18+ (for frontend)
```

### Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### Celery Setup
```bash
# In separate terminals:

# Start Celery worker
celery -A food_ordering worker --loglevel=info

# Start Celery beat (scheduler)
celery -A food_ordering beat --loglevel=info

# Monitor with Flower (optional)
pip install flower
celery -A food_ordering flower
```

### Redis Setup
```bash
# Install Redis
brew install redis  # macOS
sudo apt-get install redis-server  # Ubuntu

# Start Redis server
redis-server

# Test Redis connection
redis-cli ping  # Should return PONG
```

## Testing

### Unit Tests
```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test apps.users
python manage.py test apps.orders
```

### Load Testing
```bash
# Install locust
pip install locust

# Run load tests (example)
locust -f tests/load_tests.py --host=http://localhost:8000
```

## Monitoring & Logging

### Production Monitoring
- **Sentry**: Error tracking and performance monitoring
- **Prometheus**: Metrics collection
- **Grafana**: Dashboard and alerting
- **Django Debug Toolbar**: Development profiling

### Key Metrics to Monitor
- Response times for critical endpoints
- Cache hit rates
- Database query performance
- Celery task processing times
- User activity patterns
- Order processing bottlenecks

## Future Enhancements

### Phase 2 Features
- Mobile app (React Native)
- Push notifications
- Email notifications
- QR code ordering
- Inventory management

### Phase 3 Features
- Multi-branch support
- Vendor management
- AI demand forecasting
- Advanced reporting
- Integration APIs

## Support

For technical support or questions:
1. Check the API documentation at `/api/docs/`
2. Review the logs in `django.log`
3. Monitor Celery task status in Flower
4. Use Django admin at `/admin/` for data management

## License

MIT License - See LICENSE file for details.