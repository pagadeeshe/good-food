from datetime import datetime

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

from .constants import (
    DEFAULT_CUTOFF_TIME,
    MEAL_TYPE_CHOICES,
    ORDER_DEADLINE_DISPLAY,
    ORDER_DEADLINE_TIME,
    cutoff_display_for_meal,
    cutoff_for_meal,
)


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
    Daily menu for a specific date and meal (lunch/dinner).
    Users order today for tomorrow's menu (e.g. Sunday → Monday, Monday → Tuesday).
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
    
    date = models.DateField(db_index=True)
    meal_type = models.CharField(
        max_length=10,
        choices=MEAL_TYPE_CHOICES,
        default='lunch',
        db_index=True,
    )
    weekday = models.IntegerField(choices=WEEKDAY_CHOICES, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft', db_index=True)

    # Ordering configuration — closes at 10:00 AM on the menu date
    cutoff_time = models.TimeField(
        default=ORDER_DEADLINE_TIME,
        help_text="Order deadline on the menu date",
    )

    # When the menu was published (for admin tracking)
    published_at = models.DateTimeField(null=True, blank=True, db_index=True)

    # Menu metadata
    weekly_menu = models.ForeignKey(
        WeeklyMenu,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='daily_menus',
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
            models.Index(fields=['meal_type']),
            models.Index(fields=['date', 'meal_type']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['date', 'meal_type'],
                name='unique_daily_menu_per_meal',
            ),
        ]
        ordering = ['-date', 'meal_type']

    def __str__(self):
        return f"{self.get_meal_type_display()} menu for {self.date} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        self.weekday = self.date.weekday()
        self.cutoff_time = cutoff_for_meal(self.meal_type)
        super().save(*args, **kwargs)

    @property
    def cutoff_time_display(self):
        return cutoff_display_for_meal(self.meal_type)

    @property
    def is_editable(self):
        return self.status == 'draft'

    @property
    def ordering_deadline_at(self):
        """10:00 AM on the menu date in the local timezone."""
        if not self.date:
            return None
        naive = datetime.combine(self.date, ORDER_DEADLINE_TIME)
        return timezone.make_aware(naive, timezone.get_current_timezone())

    @property
    def expires_at(self):
        return self.ordering_deadline_at

    @property
    def expires_at_display(self):
        deadline = self.ordering_deadline_at
        if not deadline:
            return None
        local = timezone.localtime(deadline)
        return local.strftime(f'{ORDER_DEADLINE_DISPLAY} on %A, %d %b %Y')

    @property
    def ordering_deadline_message(self):
        if self.status != 'published':
            return 'Menu not yet published'
        display = self.expires_at_display
        if display:
            return f'Order before {display}'
        return f'Order before {ORDER_DEADLINE_DISPLAY} on the menu date'

    @property
    def is_ordering_open(self):
        if self.status != 'published':
            return False
        deadline = self.ordering_deadline_at
        if not deadline:
            return False
        return timezone.now() < deadline

    @property
    def orders_closed_reason(self):
        if self.status == 'draft':
            return 'Menu not yet published'
        if self.status == 'closed':
            return 'Menu closed by admin'
        if self.status == 'published':
            deadline = self.ordering_deadline_at
            if deadline and timezone.now() >= deadline:
                return (
                    f'{self.get_meal_type_display()} ordering closed — '
                    f'deadline was {self.expires_at_display}'
                )
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
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    weekday = models.IntegerField(choices=DailyMenu.WEEKDAY_CHOICES, db_index=True)
    meal_type = models.CharField(
        max_length=10,
        choices=MEAL_TYPE_CHOICES,
        default='lunch',
        db_index=True,
    )
    
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
            models.Index(fields=['weekday', 'meal_type', 'is_active']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['weekday', 'meal_type'],
                name='unique_weekday_meal_template',
            ),
        ]
        ordering = ['weekday', 'meal_type', 'name']

    def __str__(self):
        return f"{self.name} ({self.get_weekday_display()} {self.get_meal_type_display()})"


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