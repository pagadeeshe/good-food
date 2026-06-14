#!/usr/bin/env python
"""
Script to create a superuser for the Food Ordering Platform
"""
import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'food_ordering.settings_local')

# Setup Django
django.setup()

from apps.users.models import User, UserProfile

def create_admin():
    """Create admin user and sample data"""
    
    print("🚀 Creating admin user for Food Ordering Platform...")
    
    # Create admin user
    if not User.objects.filter(email='admin@foodordering.com').exists():
        admin_user = User.objects.create_user(
            email='admin@foodordering.com',
            employee_id='ADMIN001',
            first_name='Admin',
            last_name='User',
            password='admin123',
            role='admin',
            is_staff=True,
            is_superuser=True
        )
        
        # Create admin profile
        UserProfile.objects.create(
            user=admin_user,
            dietary_preferences='No restrictions',
            notification_preferences={'email': True, 'sms': False}
        )
        
        print("✅ Admin user created successfully!")
        print("📧 Email: admin@foodordering.com")
        print("🔑 Password: admin123")
    else:
        print("ℹ️  Admin user already exists")
    
    # Create sample regular user
    if not User.objects.filter(email='john@company.com').exists():
        regular_user = User.objects.create_user(
            email='john@company.com',
            employee_id='EMP001',
            first_name='John',
            last_name='Doe',
            password='user123',
            role='user'
        )
        
        UserProfile.objects.create(
            user=regular_user,
            dietary_preferences='Vegetarian',
            notification_preferences={'email': True, 'sms': True}
        )
        
        print("✅ Sample user created successfully!")
        print("📧 Email: john@company.com")
        print("🔑 Password: user123")
    else:
        print("ℹ️  Sample user already exists")
    
    print("\n🎉 Setup completed! You can now:")
    print("1. Access Django Admin: http://localhost:8000/admin/")
    print("2. View the platform: http://localhost:8000/")
    print("3. Start the development server: python manage.py runserver --settings=food_ordering.settings_local")

if __name__ == '__main__':
    create_admin()