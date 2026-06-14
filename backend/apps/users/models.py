from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator


class CustomUserManager(BaseUserManager):
    """
    Custom user manager for email-based authentication
    """
    
    def create_user(self, email, employee_id, first_name, last_name, password=None, **extra_fields):
        """Create and return a regular user with an email and password."""
        if not email:
            raise ValueError('The Email field must be set')
        if not employee_id:
            raise ValueError('The Employee ID field must be set')
        
        email = self.normalize_email(email)
        user = self.model(
            email=email,
            employee_id=employee_id.upper(),
            first_name=first_name,
            last_name=last_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, employee_id, first_name, last_name, password=None, **extra_fields):
        """Create and return a superuser with an email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, employee_id, first_name, last_name, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model for the food ordering platform.
    Supports 10,000+ users with role-based permissions.
    """
    
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('user', 'User'),
    ]
    
    # Remove username field, use email for authentication
    username = None
    
    # Core fields
    email = models.EmailField(unique=True, db_index=True)
    employee_id = models.CharField(
        max_length=20, 
        unique=True, 
        db_index=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Z0-9]{3,20}$',
                message='Employee ID must contain only uppercase letters and numbers, 3-20 characters.'
            )
        ]
    )
    
    # Personal Information
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(
        max_length=15,
        blank=True,
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Phone number must be entered in the format: "+999999999". Up to 15 digits allowed.'
            )
        ]
    )
    
    # Role and Status
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)
    
    # Custom manager
    objects = CustomUserManager()
    
    # Authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['employee_id', 'first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['employee_id']),
            models.Index(fields=['role']),
            models.Index(fields=['is_active']),
        ]
        
    def __str__(self):
        return f"{self.get_full_name()} ({self.employee_id})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def is_admin(self):
        return self.role == 'admin'
    
    @property
    def is_regular_user(self):
        return self.role == 'user'


class UserProfile(models.Model):
    """
    Extended user profile for additional information.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Preferences
    dietary_preferences = models.TextField(blank=True, help_text="Any dietary restrictions or preferences")
    notification_preferences = models.JSONField(default=dict, help_text="Email, SMS notification settings")
    
    # Statistics (for reporting)
    total_orders = models.PositiveIntegerField(default=0)
    last_order_date = models.DateField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_profiles'
        
    def __str__(self):
        return f"Profile for {self.user.get_full_name()}"