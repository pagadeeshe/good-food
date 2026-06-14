from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.db.models import Sum, F


class Order(models.Model):
    """
    User orders for daily menus.
    Designed to handle 2000+ concurrent users and 500+ orders per minute.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    # Core relationships
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='orders', db_index=True)
    daily_menu = models.ForeignKey('menu.DailyMenu', on_delete=models.CASCADE, related_name='orders', db_index=True)
    
    # Order details
    order_date = models.DateField(db_index=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending', db_index=True)
    
    # Order summary (denormalized for performance)
    total_items = models.PositiveIntegerField(default=0)
    
    # Notes
    notes = models.TextField(blank=True, help_text="Special instructions or notes")
    
    # Admin fields
    admin_notes = models.TextField(blank=True, help_text="Admin-only notes")
    cancelled_reason = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'orders'
        indexes = [
            models.Index(fields=['user', 'order_date']),
            models.Index(fields=['daily_menu', 'status']),
            models.Index(fields=['order_date', 'status']),
            models.Index(fields=['created_at']),
        ]
        # Ensure one order per user per day
        unique_together = [['user', 'daily_menu']]
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Order #{self.id} - {self.user.get_full_name()} ({self.order_date})"
    
    def save(self, *args, **kwargs):
        # Set order_date from daily_menu if not provided
        if not self.order_date:
            self.order_date = self.daily_menu.date
        
        # Set confirmed_at when status changes to confirmed
        if self.status == 'confirmed' and not self.confirmed_at:
            self.confirmed_at = timezone.now()
        
        # Set cancelled_at when status changes to cancelled
        if self.status == 'cancelled' and not self.cancelled_at:
            self.cancelled_at = timezone.now()
        
        super().save(*args, **kwargs)
    
    @property
    def can_be_modified(self):
        """Orders are final once placed — no edits until the next menu."""
        if self.order_items.exists():
            return False
        return (
            self.status in ['pending', 'confirmed']
            and self.daily_menu.is_ordering_open
        )
    
    @property
    def can_be_cancelled(self):
        """Check if order can be cancelled."""
        return self.can_be_modified and self.status != 'cancelled'
    
    def get_total_quantity(self):
        """Get total quantity of all items in this order."""
        return self.order_items.aggregate(
            total=Sum('quantity')
        )['total'] or 0
    
    def update_total_items(self):
        """Update denormalized total_items field."""
        self.total_items = self.get_total_quantity()
        self.save(update_fields=['total_items'])
    
    def confirm(self):
        """Confirm the order."""
        if self.status == 'pending':
            self.status = 'confirmed'
            self.confirmed_at = timezone.now()
            self.save(update_fields=['status', 'confirmed_at', 'updated_at'])
    
    def cancel(self, reason=''):
        """Cancel the order."""
        if self.can_be_cancelled:
            self.status = 'cancelled'
            self.cancelled_at = timezone.now()
            if reason:
                self.cancelled_reason = reason
            self.save(update_fields=['status', 'cancelled_at', 'cancelled_reason', 'updated_at'])


class OrderItem(models.Model):
    """
    Individual items within an order.
    Optimized for high-frequency reads and writes.
    """
    
    # Core relationships
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items', db_index=True)
    menu_item = models.ForeignKey('menu.MenuItem', on_delete=models.CASCADE, related_name='order_items', db_index=True)
    
    # Item details (denormalized for performance and historical accuracy)
    item_name = models.CharField(max_length=100)  # Store name at time of order
    item_category = models.CharField(max_length=20)
    
    # Quantity
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(20)],
        help_text="Quantity ordered"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'order_items'
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['menu_item']),
            models.Index(fields=['item_name']),
        ]
        # Ensure one item per order (user can't order same item multiple times in one order)
        unique_together = [['order', 'menu_item']]
        ordering = ['menu_item__sort_order', 'item_name']
        
    def __str__(self):
        return f"{self.quantity}x {self.item_name} (Order #{self.order.id})"
    
    def save(self, *args, **kwargs):
        # Denormalize item details for historical accuracy and performance
        if not self.item_name:
            self.item_name = self.menu_item.name
        if not self.item_category:
            self.item_category = self.menu_item.category
        
        super().save(*args, **kwargs)
        
        # Update order total
        self.order.update_total_items()


class OrderSummary(models.Model):
    """
    Pre-computed monthly summaries for users.
    Cached for performance with 10,000+ users.
    """
    
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='order_summaries')
    
    # Time period
    year = models.PositiveIntegerField(db_index=True)
    month = models.PositiveIntegerField(db_index=True)
    
    # Summary data (JSON for flexibility)
    summary_data = models.JSONField(default=dict, help_text="Aggregated order data for the month")
    
    # Quick stats (denormalized for performance)
    total_orders = models.PositiveIntegerField(default=0)
    total_items = models.PositiveIntegerField(default=0)
    unique_items_ordered = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'order_summaries'
        indexes = [
            models.Index(fields=['user', 'year', 'month']),
            models.Index(fields=['year', 'month']),
        ]
        unique_together = [['user', 'year', 'month']]
        ordering = ['-year', '-month']
        
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.year}/{self.month:02d}"


class DailyOrderReport(models.Model):
    """
    Pre-computed daily order reports for admin analytics.
    Shows total quantities needed for kitchen preparation.
    """
    
    daily_menu = models.OneToOneField(
        'menu.DailyMenu', 
        on_delete=models.CASCADE, 
        related_name='order_report'
    )
    
    # Summary statistics
    total_orders = models.PositiveIntegerField(default=0)
    total_users = models.PositiveIntegerField(default=0)
    total_items = models.PositiveIntegerField(default=0)
    
    # Item-wise breakdown (JSON for flexibility)
    item_breakdown = models.JSONField(
        default=dict,
        help_text="Item-wise quantities: {item_name: {quantity: X, orders: Y, users: Z}}"
    )
    
    # Category-wise breakdown
    category_breakdown = models.JSONField(
        default=dict,
        help_text="Category-wise totals"
    )
    
    # Status
    is_finalized = models.BooleanField(default=False, help_text="Report is final (no more changes expected)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'daily_order_reports'
        indexes = [
            models.Index(fields=['daily_menu']),
            models.Index(fields=['is_finalized']),
        ]
        ordering = ['-created_at']
        
    def __str__(self):
        return f"Order Report for {self.daily_menu.date}"
    
    def generate_report(self):
        """Generate/regenerate the order report for this daily menu."""
        from django.db.models import Count, Sum
        
        # Get all orders for this daily menu
        orders = self.daily_menu.orders.filter(status__in=['confirmed', 'completed'])
        
        # Basic statistics
        self.total_orders = orders.count()
        self.total_users = orders.values('user').distinct().count()
        self.total_items = orders.aggregate(Sum('total_items'))['total_items'] or 0
        
        # Item-wise breakdown
        item_breakdown = {}
        order_items = OrderItem.objects.filter(
            order__daily_menu=self.daily_menu,
            order__status__in=['confirmed', 'completed']
        ).values('item_name', 'item_category').annotate(
            total_quantity=Sum('quantity'),
            order_count=Count('order', distinct=True),
            user_count=Count('order__user', distinct=True)
        )
        
        for item in order_items:
            item_breakdown[item['item_name']] = {
                'quantity': item['total_quantity'],
                'orders': item['order_count'],
                'users': item['user_count'],
                'category': item['item_category']
            }
        
        self.item_breakdown = item_breakdown
        
        # Category-wise breakdown
        category_breakdown = {}
        for item_name, item_data in item_breakdown.items():
            category = item_data['category']
            if category not in category_breakdown:
                category_breakdown[category] = {
                    'total_quantity': 0,
                    'unique_items': 0,
                    'orders': 0,
                    'users': set()
                }
            
            category_breakdown[category]['total_quantity'] += item_data['quantity']
            category_breakdown[category]['unique_items'] += 1
            category_breakdown[category]['orders'] += item_data['orders']
            category_breakdown[category]['users'].update([item_data['users']])
        
        # Convert sets to counts for JSON serialization
        for category_data in category_breakdown.values():
            category_data['unique_users'] = len(category_data['users'])
            del category_data['users']
        
        self.category_breakdown = category_breakdown
        
        self.save()
        
    def finalize_report(self):
        """Mark report as finalized (typically after cutoff time)."""
        self.generate_report()
        self.is_finalized = True
        self.save(update_fields=['is_finalized', 'updated_at'])