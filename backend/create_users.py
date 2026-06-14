# Simple user creation script
# Run with: python manage.py shell --settings=food_ordering.settings_local < create_users.py

from django.conf import settings
from apps.users.models import User, UserProfile

admin_email = settings.ADMIN_EMAIL
print(f"Standard admin email: {admin_email}")

# Demote any other admin accounts
demoted = User.objects.filter(role='admin').exclude(email__iexact=admin_email).update(
    role='user', is_staff=False, is_superuser=False
)
if demoted:
    print(f"Demoted {demoted} non-standard admin(s) to user role")

# Create standard admin
admin_user, created = User.objects.get_or_create(
    email=admin_email,
    defaults={
        'employee_id': 'ADMIN001',
        'first_name': 'Admin',
        'last_name': 'User',
        'role': 'admin',
        'is_staff': True,
        'is_superuser': True,
    },
)
if created:
    admin_user.set_password('admin123')
    admin_user.save()
    UserProfile.objects.create(user=admin_user)
    print(f"✅ Admin created: {admin_email} / admin123")
else:
    admin_user.role = 'admin'
    admin_user.is_staff = True
    admin_user.is_superuser = True
    admin_user.save()
    print(f"ℹ️ Standard admin verified: {admin_email}")

# Create sample user
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
    print("✅ User created: john@company.com / user123")
else:
    print("ℹ️ User already exists")

print("🎉 Setup completed!")
