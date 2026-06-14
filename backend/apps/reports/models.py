from django.db import models
from django.utils import timezone


class Report(models.Model):
    """
    Generated reports for admin analytics.
    """
    
    REPORT_TYPE_CHOICES = [
        ('daily_orders', 'Daily Orders Report'),
        ('weekly_summary', 'Weekly Summary'),
        ('monthly_summary', 'Monthly Summary'),
        ('user_analytics', 'User Analytics'),
        ('item_popularity', 'Item Popularity Report'),
        ('kitchen_requirements', 'Kitchen Requirements'),
    ]
    
    FORMAT_CHOICES = [
        ('json', 'JSON'),
        ('csv', 'CSV'),
        ('xlsx', 'Excel'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Report metadata
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES, db_index=True)
    format = models.CharField(max_length=10, choices=FORMAT_CHOICES, default='json')
    
    # Parameters (JSON for flexibility)
    parameters = models.JSONField(default=dict, help_text="Report parameters like date range, filters")
    
    # Status and results
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending', db_index=True)
    file_path = models.CharField(max_length=500, blank=True, help_text="Path to generated report file")
    data = models.JSONField(default=dict, help_text="Report data if small enough to store in DB")
    error_message = models.TextField(blank=True)
    
    # Metadata
    requested_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='requested_reports')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'reports'
        indexes = [
            models.Index(fields=['report_type', 'status']),
            models.Index(fields=['requested_by']),
            models.Index(fields=['created_at']),
        ]
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"
    
    def mark_processing(self):
        """Mark report as processing."""
        self.status = 'processing'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def mark_completed(self, data=None, file_path=None):
        """Mark report as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        if data:
            self.data = data
        if file_path:
            self.file_path = file_path
        self.save(update_fields=['status', 'completed_at', 'data', 'file_path'])
    
    def mark_failed(self, error_message):
        """Mark report as failed."""
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save(update_fields=['status', 'completed_at', 'error_message'])


class UserAnalytics(models.Model):
    """
    Pre-computed user analytics for performance.
    Updated daily via background tasks.
    """
    
    user = models.OneToOneField('users.User', on_delete=models.CASCADE, related_name='analytics')
    
    # Order statistics
    total_orders = models.PositiveIntegerField(default=0)
    total_items_ordered = models.PositiveIntegerField(default=0)
    average_items_per_order = models.FloatField(default=0.0)
    
    # Time-based statistics
    first_order_date = models.DateField(null=True, blank=True)
    last_order_date = models.DateField(null=True, blank=True)
    days_since_last_order = models.PositiveIntegerField(default=0)
    
    # Activity patterns (JSON for flexibility)
    monthly_breakdown = models.JSONField(default=dict, help_text="Monthly order counts")
    favorite_items = models.JSONField(default=list, help_text="Most frequently ordered items")
    weekday_patterns = models.JSONField(default=dict, help_text="Orders by day of week")
    
    # Computed statistics
    is_regular_user = models.BooleanField(default=False, help_text="Orders frequently")
    is_inactive_user = models.BooleanField(default=False, help_text="Hasn't ordered recently")
    
    # Timestamps
    last_computed_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_analytics'
        
    def __str__(self):
        return f"Analytics for {self.user.get_full_name()}"
    
    def compute_analytics(self):
        """Recompute analytics for this user."""
        from apps.orders.models import Order, OrderItem
        from django.db.models import Count, Sum, Avg
        from datetime import date, timedelta
        
        # Get all confirmed/completed orders
        orders = Order.objects.filter(
            user=self.user,
            status__in=['confirmed', 'completed']
        )
        
        # Basic statistics
        self.total_orders = orders.count()
        self.total_items_ordered = orders.aggregate(Sum('total_items'))['total_items'] or 0
        
        if self.total_orders > 0:
            self.average_items_per_order = self.total_items_ordered / self.total_orders
            self.first_order_date = orders.earliest('order_date').order_date
            self.last_order_date = orders.latest('order_date').order_date
            
            # Days since last order
            if self.last_order_date:
                self.days_since_last_order = (date.today() - self.last_order_date).days
        
        # Activity patterns
        self._compute_monthly_breakdown()
        self._compute_favorite_items()
        self._compute_weekday_patterns()
        
        # User classification
        self.is_regular_user = self.total_orders >= 10 and self.days_since_last_order <= 7
        self.is_inactive_user = self.days_since_last_order > 30
        
        self.save()
    
    def _compute_monthly_breakdown(self):
        """Compute monthly order breakdown."""
        from apps.orders.models import Order
        from django.db.models import Count
        from datetime import date
        import calendar
        
        monthly_data = {}
        current_date = date.today()
        
        # Get last 12 months of data
        for i in range(12):
            year = current_date.year
            month = current_date.month
            
            month_orders = Order.objects.filter(
                user=self.user,
                order_date__year=year,
                order_date__month=month,
                status__in=['confirmed', 'completed']
            ).count()
            
            month_key = f"{year}-{month:02d}"
            monthly_data[month_key] = month_orders
            
            # Move to previous month
            if month == 1:
                current_date = current_date.replace(year=year-1, month=12)
            else:
                current_date = current_date.replace(month=month-1)
        
        self.monthly_breakdown = monthly_data
    
    def _compute_favorite_items(self):
        """Compute most frequently ordered items."""
        from apps.orders.models import OrderItem
        from django.db.models import Sum
        
        favorite_items = list(
            OrderItem.objects.filter(
                order__user=self.user,
                order__status__in=['confirmed', 'completed']
            ).values('item_name').annotate(
                total_quantity=Sum('quantity'),
                order_count=Count('order', distinct=True)
            ).order_by('-total_quantity')[:10]
        )
        
        self.favorite_items = favorite_items
    
    def _compute_weekday_patterns(self):
        """Compute ordering patterns by weekday."""
        from apps.orders.models import Order
        from django.db.models import Count
        
        weekday_data = {}
        weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        
        for i, day_name in enumerate(weekdays):
            day_orders = Order.objects.filter(
                user=self.user,
                order_date__week_day=(i+2) % 7 + 1,  # Django weekday: 1=Sunday, 2=Monday...
                status__in=['confirmed', 'completed']
            ).count()
            
            weekday_data[day_name] = day_orders
        
        self.weekday_patterns = weekday_data