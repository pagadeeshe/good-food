from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import time


class WeeklyMenu(models.Model):
    """
    Weekly menu template that can be used to generate daily menus.
    """
    
    name = models.CharField(max_length=100, help_text="e.g., 'Week of June 10-16, 2024'")
    week_start_date = models.DateField(db_index=True)
    description = models.TextField(blank=True)
    
    # Metadata
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='created_weekly_menus')
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'weekly_menus'
        indexes = [
            models.Index(fields=['week_start_date']),
            models.Index(fields=['is_active']),
        ]
        ordering = ['-week_start_date']
        
    def __str__(self):
        return f"{self.name} (Starting {self.week_start_date})"


class DailyMenu(models.Model):
    """
    Daily menu for a specific date.
    Users can only see and order from today's active menu.
    """
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('closed', 'Closed'),
    ]
    
    WEEKDAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    date = models.DateField(unique=True, db_index=True)
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', db_index=True)
    
    # Ordering configuration
    cutoff_time = models.TimeField(default=time(11, 0), help_text="Time until which orders can be placed")
    
    # Menu metadata
    weekly_menu = models.ForeignKey(
        WeeklyMenu, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='daily_menus'
    )
    description = models.TextField(blank=True)
    
    # Statistics (denormalized for performance)
    total_orders = models.PositiveIntegerField(default=0)
    total_items_ordered = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='created_daily_menus')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'daily_menus'
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['status']),
            models.Index(fields=['weekday']),
        ]
        ordering = ['-date']
        
    def __str__(self):
        return f"Menu for {self.date} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Auto-set weekday
        self.weekday = self.date.weekday()
        super().save(*args, **kwargs)
    
    @property
    def is_ordering_open(self):
        """Check if ordering is still open for this menu."""
        if self.status != 'published':
            return False
        
        now = timezone.now()
        today = now.date()
        current_time = now.time()
        
        # Only allow orders for today's menu before cutoff time
        return self.date == today and current_time <= self.cutoff_time
    
    @property
    def orders_closed_reason(self):
        """Get reason why orders are closed."""
        if self.status == 'draft':
            return "Menu not yet published"
        elif self.status == 'closed':
            return "Menu closed by admin"
        
        now = timezone.now()
        today = now.date()
        current_time = now.time()
        
        if self.date < today:
            return "Past date"
        elif self.date > today:
            return "Future date - only today's menu is available"
        elif current_time > self.cutoff_time:
            return f"Ordering closed at {self.cutoff_time.strftime('%H:%M')}"
        
        return None


class MenuItem(models.Model):
    """
    Individual food items available in a daily menu.
    """
    
    CATEGORY_CHOICES = [
        ('main', 'Main Course'),
        ('rice', 'Rice'),
        ('curry', 'Curry'),
        ('side', 'Side Dish'),
        ('dessert', 'Dessert'),
        ('beverage', 'Beverage'),
    ]
    
    daily_menu = models.ForeignKey(DailyMenu, on_delete=models.CASCADE, related_name='menu_items')
    
    # Item details
    name = models.CharField(max_length=100, db_index=True)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='main', db_index=True)
    
    # Availability
    is_available = models.BooleanField(default=True, db_index=True)
    max_quantity_per_user = models.PositiveIntegerField(
        default=5,
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text="Maximum quantity a single user can order"
    )
    
    # Statistics (denormalized for performance)
    total_ordered = models.PositiveIntegerField(default=0)
    unique_orders = models.PositiveIntegerField(default=0)  # Number of unique users who ordered this item
    
    # Ordering
    sort_order = models.PositiveIntegerField(default=0, help_text="Order in which items appear in menu")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'menu_items'
        indexes = [
            models.Index(fields=['daily_menu', 'is_available']),
            models.Index(fields=['category']),
            models.Index(fields=['name']),
            models.Index(fields=['sort_order']),
        ]
        ordering = ['sort_order', 'name']
        
    def __str__(self):
        return f"{self.name} ({self.daily_menu.date})"
    
    @property
    def can_be_ordered(self):
        """Check if this item can currently be ordered."""
        return (
            self.is_available and 
            self.daily_menu.is_ordering_open
        )


class MenuTemplate(models.Model):
    """
    Reusable menu templates for quick menu creation.
    Useful for recurring weekly menus.
    """
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    weekday = models.IntegerField(choices=DailyMenu.WEEKDAY_CHOICES, db_index=True)
    
    # Template metadata
    is_active = models.BooleanField(default=True)
    usage_count = models.PositiveIntegerField(default=0)
    
    # Metadata
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='created_menu_templates')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'menu_templates'
        indexes = [
            models.Index(fields=['weekday', 'is_active']),
        ]
        ordering = ['weekday', 'name']
        
    def __str__(self):
        return f"{self.name} ({self.get_weekday_display()})"


class MenuTemplateItem(models.Model):
    """
    Items in a menu template.
    """
    
    template = models.ForeignKey(MenuTemplate, on_delete=models.CASCADE, related_name='template_items')
    
    # Item details (similar to MenuItem but as template)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=MenuItem.CATEGORY_CHOICES, default='main')
    max_quantity_per_user = models.PositiveIntegerField(default=5)
    sort_order = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'menu_template_items'
        ordering = ['sort_order', 'name']
        
    def __str__(self):
        return f"{self.name} (Template: {self.template.name})"