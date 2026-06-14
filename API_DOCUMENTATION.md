# Food Ordering Platform - API Documentation

## Base URL
```
Development: http://localhost:8000/api
Production: https://your-domain.com/api
```

## Authentication

### JWT Token Authentication
All authenticated endpoints require a valid JWT token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### Token Endpoints

#### Login
```http
POST /api/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "employee_id": "EMP001",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "role": "user",
    "is_active": true
  }
}
```

#### Refresh Token
```http
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

#### Logout
```http
POST /api/auth/logout/
Authorization: Bearer <access_token>

{
  "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## User Management

### Get Current User Profile
```http
GET /api/users/me/
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 1,
  "employee_id": "EMP001",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "full_name": "John Doe",
  "phone_number": "+1234567890",
  "role": "user",
  "is_active": true,
  "last_login": "2024-06-14T10:30:00Z",
  "date_joined": "2024-01-15T08:00:00Z",
  "profile": {
    "dietary_preferences": "Vegetarian",
    "total_orders": 15,
    "last_order_date": "2024-06-13"
  }
}
```

### Update Profile
```http
PATCH /api/users/me/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Smith",
  "phone_number": "+1987654321"
}
```

### Admin: List All Users
```http
GET /api/users/?search=john&role=user&is_active=true&page=1
Authorization: Bearer <admin_access_token>
```

**Query Parameters:**
- `search`: Search by name, email, or employee ID
- `role`: Filter by role (`admin` or `user`)
- `is_active`: Filter by active status (`true` or `false`)
- `page`: Page number for pagination

**Response:**
```json
{
  "count": 50,
  "next": "http://localhost:8000/api/users/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "employee_id": "EMP001",
      "email": "john@example.com",
      "full_name": "John Doe",
      "role": "user",
      "is_active": true,
      "total_orders": 15,
      "last_login": "2024-06-14T10:30:00Z"
    }
  ]
}
```

## Menu Management

### Get Today's Menu
```http
GET /api/menu/today/
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "id": 1,
  "date": "2024-06-14",
  "status": "published",
  "cutoff_time": "11:00:00",
  "description": "Today's special menu",
  "is_ordering_open": true,
  "orders_closed_reason": null,
  "available_items": [
    {
      "id": 1,
      "name": "Chicken Curry",
      "description": "Spicy chicken curry with rice",
      "category": "main",
      "is_available": true,
      "max_quantity_per_user": 3,
      "total_ordered": 45,
      "can_be_ordered": true
    },
    {
      "id": 2,
      "name": "White Rice",
      "description": "Steamed white rice",
      "category": "rice",
      "is_available": true,
      "max_quantity_per_user": 2,
      "total_ordered": 48,
      "can_be_ordered": true
    }
  ]
}
```

### Admin: Create Daily Menu
```http
POST /api/menu/daily/
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{
  "date": "2024-06-15",
  "status": "draft",
  "cutoff_time": "11:00:00",
  "description": "Weekend special menu",
  "menu_items": [
    {
      "name": "Fish Curry",
      "description": "Fresh fish curry",
      "category": "main",
      "max_quantity_per_user": 2,
      "sort_order": 1
    }
  ]
}
```

### Admin: Create Menu from Template
```http
POST /api/menu/from-template/
Authorization: Bearer <admin_access_token>
Content-Type: application/json

{
  "template_id": 1,
  "date": "2024-06-15",
  "cutoff_time": "11:00:00",
  "description": "Menu created from Monday template"
}
```

### Admin: Publish Menu
```http
POST /api/menu/daily/1/publish/
Authorization: Bearer <admin_access_token>
```

## Order Management

### Place Order
```http
POST /api/orders/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "daily_menu_id": 1,
  "items": [
    {
      "menu_item_id": 1,
      "quantity": 2
    },
    {
      "menu_item_id": 2,
      "quantity": 1
    }
  ],
  "notes": "Extra spicy please"
}
```

**Response:**
```json
{
  "id": 1,
  "user": {
    "id": 1,
    "employee_id": "EMP001",
    "full_name": "John Doe"
  },
  "daily_menu": {
    "id": 1,
    "date": "2024-06-14"
  },
  "status": "confirmed",
  "total_items": 3,
  "notes": "Extra spicy please",
  "order_items": [
    {
      "id": 1,
      "item_name": "Chicken Curry",
      "item_category": "main",
      "quantity": 2
    },
    {
      "id": 2,
      "item_name": "White Rice",
      "item_category": "rice",
      "quantity": 1
    }
  ],
  "can_be_modified": true,
  "created_at": "2024-06-14T09:30:00Z"
}
```

### Get User Orders
```http
GET /api/orders/?date=2024-06-14&status=confirmed&page=1
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `date`: Filter by order date
- `status`: Filter by order status
- `page`: Page number

### Update Order
```http
PUT /api/orders/1/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "items": [
    {
      "menu_item_id": 1,
      "quantity": 1
    }
  ],
  "notes": "Reduced quantity"
}
```

### Cancel Order
```http
DELETE /api/orders/1/
Authorization: Bearer <access_token>
```

### Get Monthly Summary
```http
GET /api/orders/monthly-summary/?year=2024&month=6
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "year": 2024,
  "month": 6,
  "total_orders": 15,
  "total_items": 45,
  "summary_data": {
    "items": {
      "Chicken Curry": {
        "quantity": 20,
        "orders": 12
      },
      "White Rice": {
        "quantity": 25,
        "orders": 15
      }
    }
  }
}
```

## Reports & Analytics (Admin Only)

### Daily Order Report
```http
GET /api/reports/daily/2024-06-14/
Authorization: Bearer <admin_access_token>
```

**Response:**
```json
{
  "date": "2024-06-14",
  "total_orders": 150,
  "total_users": 142,
  "total_items": 380,
  "item_breakdown": {
    "Chicken Curry": {
      "quantity": 180,
      "orders": 120,
      "users": 120,
      "category": "main"
    },
    "White Rice": {
      "quantity": 200,
      "orders": 150,
      "users": 150,
      "category": "rice"
    }
  },
  "category_breakdown": {
    "main": {
      "total_quantity": 180,
      "unique_items": 1,
      "orders": 120,
      "unique_users": 120
    },
    "rice": {
      "total_quantity": 200,
      "unique_items": 1,
      "orders": 150,
      "unique_users": 150
    }
  },
  "is_finalized": true
}
```

### User Statistics
```http
GET /api/users/statistics/
Authorization: Bearer <admin_access_token>
```

**Response:**
```json
{
  "total_users": 1000,
  "active_users": 950,
  "inactive_users": 50,
  "admin_users": 5,
  "regular_users": 995,
  "recent_registrations": 25,
  "users_with_orders_this_month": 800,
  "last_updated": "2024-06-14T12:00:00Z"
}
```

### Menu Statistics
```http
GET /api/menu/statistics/
Authorization: Bearer <admin_access_token>
```

**Response:**
```json
{
  "total_menus": 100,
  "published_menus": 85,
  "draft_menus": 15,
  "total_items": 500,
  "most_popular_items": [
    {
      "name": "Chicken Curry",
      "total_ordered": 1500,
      "category": "main"
    }
  ],
  "recent_menus": [
    {
      "id": 1,
      "date": "2024-06-14",
      "status": "published",
      "total_orders": 150,
      "created_by": "Admin User"
    }
  ]
}
```

### Top Users by Orders
```http
GET /api/users/top/?limit=10
Authorization: Bearer <admin_access_token>
```

### Inactive Users
```http
GET /api/users/inactive/
Authorization: Bearer <admin_access_token>
```

## Error Responses

### Standard Error Format
```json
{
  "error": "Error message description",
  "details": {
    "field_name": ["Specific field error"]
  }
}
```

### Common HTTP Status Codes
- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### Authentication Errors
```json
{
  "error": "Invalid credentials",
  "code": "authentication_failed"
}
```

### Validation Errors
```json
{
  "error": "Validation failed",
  "details": {
    "email": ["This field is required."],
    "quantity": ["Ensure this value is less than or equal to 5."]
  }
}
```

### Rate Limiting
```json
{
  "error": "Rate limit exceeded",
  "retry_after": 60
}
```

## Rate Limits

### Authentication Endpoints
- Login: 5 attempts per minute per IP
- Registration: 3 registrations per hour per IP
- Password reset: 3 requests per hour per IP

### API Endpoints
- General API: 100 requests per minute per user
- Order placement: 10 requests per minute per user
- Anonymous requests: 100 requests per hour per IP

## Pagination

List endpoints use cursor-based pagination:

```json
{
  "count": 250,
  "next": "http://localhost:8000/api/users/?cursor=eyJ1c2VyX2lkIjoxMH0%3D",
  "previous": null,
  "results": [...]
}
```

## Filtering and Search

### Common Query Parameters
- `search`: Full-text search across relevant fields
- `ordering`: Sort by field (prefix with `-` for descending)
- `page_size`: Items per page (max 100)

### Date Filtering
- `date`: Specific date (YYYY-MM-DD)
- `date__gte`: From date (greater than or equal)
- `date__lte`: To date (less than or equal)
- `date__range`: Date range (comma-separated)

## WebSocket Support (Future)

Real-time updates for order status changes and menu updates will be available via WebSocket connections:

```javascript
const socket = new WebSocket('ws://localhost:8000/ws/orders/');
socket.onmessage = function(event) {
  const data = JSON.parse(event.data);
  // Handle real-time updates
};
```

## SDK Examples

### JavaScript/TypeScript
```javascript
const API_BASE = 'http://localhost:8000/api';

class FoodOrderingAPI {
  constructor(accessToken) {
    this.accessToken = accessToken;
  }

  async getTodayMenu() {
    const response = await fetch(`${API_BASE}/menu/today/`, {
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json'
      }
    });
    return response.json();
  }

  async placeOrder(orderData) {
    const response = await fetch(`${API_BASE}/orders/`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.accessToken}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(orderData)
    });
    return response.json();
  }
}
```

### Python
```python
import requests

class FoodOrderingClient:
    def __init__(self, base_url, access_token):
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
    
    def get_today_menu(self):
        response = requests.get(
            f'{self.base_url}/menu/today/',
            headers=self.headers
        )
        return response.json()
    
    def place_order(self, order_data):
        response = requests.post(
            f'{self.base_url}/orders/',
            json=order_data,
            headers=self.headers
        )
        return response.json()
```

## Testing

### Postman Collection
Import the Postman collection from `/docs/postman_collection.json` for easy API testing.

### cURL Examples

#### Login
```bash
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

#### Get Today's Menu
```bash
curl -X GET http://localhost:8000/api/menu/today/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

#### Place Order
```bash
curl -X POST http://localhost:8000/api/orders/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "daily_menu_id": 1,
    "items": [
      {"menu_item_id": 1, "quantity": 2},
      {"menu_item_id": 2, "quantity": 1}
    ],
    "notes": "Extra spicy"
  }'
```