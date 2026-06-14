"""
Celery tasks for order processing and analytics.
Designed for high-performance with 2000+ concurrent users.
"""

from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Sum, F
from django.core.cache import cache
from datetime import date, timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def generate_daily_order_report(self, daily_menu_id):
    """
    Generate order report for a specific daily menu.
    Called when cutoff time is reached or menu is closed.
    """
    try:
        from .models import DailyMenu, DailyOrderReport
        
        daily_menu = DailyMenu.objects.get(id=daily_menu_id)
        
        # Get or create report
        report, created = DailyOrderReport.objects.get_or_create(
            daily_menu=daily_menu
        )
        
        # Generate the report
        report.generate_report()
        
        # Clear related caches
        cache_keys = [
            f"daily_menu_{daily_menu.date}",
            f"today_menu_{daily_menu.date}",
            "admin_dashboard_stats",
        ]
        cache.delete_many(cache_keys)
        
        logger.info(f"Generated order report for {daily_menu.date}")
        return f"Report generated for {daily_menu.date}"
        
    except Exception as exc:
        logger.error(f"Failed to generate report for menu {daily_menu_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True)
def generate_daily_order_reports(self):
    """
    Generate reports for all active daily menus.
    Runs hourly via Celery Beat.
    """
    try:
        from .models import DailyMenu
        
        # Get menus that need reports
        today = timezone.now().date()
        menus_needing_reports = DailyMenu.objects.filter(
            date__lte=today,
            status='published'
        ).exclude(
            order_report__isnull=False
        )
        
        reports_generated = 0
        for menu in menus_needing_reports:
            generate_daily_order_report.delay(menu.id)
            reports_generated += 1
        
        logger.info(f"Queued {reports_generated} daily reports for generation")
        return f"Queued {reports_generated} reports"
        
    except Exception as exc:
        logger.error(f"Failed to queue daily reports: {exc}")
        return f"Error: {exc}"


@shared_task(bind=True, max_retries=3)
def update_order_statistics(self, order_id):
    """
    Update denormalized statistics when order is placed/modified.
    Called asynchronously to avoid blocking order placement.
    """
    try:
        from .models import Order, OrderItem
        from apps.menu.models import MenuItem, DailyMenu
        from apps.users.models import UserProfile
        
        order = Order.objects.select_related('user', 'daily_menu').get(id=order_id)
        
        # Update user profile statistics
        profile, created = UserProfile.objects.get_or_create(user=order.user)
        
        if order.status in ['confirmed', 'completed']:
            profile.total_orders = order.user.orders.filter(
                status__in=['confirmed', 'completed']
            ).count()
            profile.last_order_date = order.order_date
            profile.save(update_fields=['total_orders', 'last_order_date'])
        
        # Update menu item statistics
        order_items = OrderItem.objects.filter(order=order)
        for item in order_items:
            menu_item = item.menu_item
            
            if order.status in ['confirmed', 'completed']:
                # Recalculate statistics
                menu_item.total_ordered = OrderItem.objects.filter(
                    menu_item=menu_item,
                    order__status__in=['confirmed', 'completed']
                ).aggregate(Sum('quantity'))['quantity__sum'] or 0
                
                menu_item.unique_orders = OrderItem.objects.filter(
                    menu_item=menu_item,
                    order__status__in=['confirmed', 'completed']
                ).values('order').distinct().count()
                
                menu_item.save(update_fields=['total_ordered', 'unique_orders'])
        
        # Update daily menu statistics
        daily_menu = order.daily_menu
        daily_menu.total_orders = daily_menu.orders.filter(
            status__in=['confirmed', 'completed']
        ).count()
        
        daily_menu.total_items_ordered = daily_menu.orders.filter(
            status__in=['confirmed', 'completed']
        ).aggregate(Sum('total_items'))['total_items__sum'] or 0
        
        daily_menu.save(update_fields=['total_orders', 'total_items_ordered'])
        
        # Clear relevant caches
        cache_keys = [
            f"user_profile_{order.user.id}",
            f"daily_menu_{daily_menu.date}",
            f"menu_item_{menu_item.id}" for menu_item in [item.menu_item for item in order_items]
        ]
        cache.delete_many(cache_keys)
        
        logger.info(f"Updated statistics for order {order_id}")
        return f"Statistics updated for order {order_id}"
        
    except Exception as exc:
        logger.error(f"Failed to update statistics for order {order_id}: {exc}")
        raise self.retry(exc=exc, countdown=30)


@shared_task(bind=True)
def generate_monthly_summaries(self, year, month):
    """
    Generate monthly order summaries for all users.
    Called at the end of each month.
    """
    try:
        from .models import Order, OrderItem, OrderSummary
        from apps.users.models import User
        from django.db.models import Count, Sum
        
        # Get all users who placed orders in the given month
        users_with_orders = User.objects.filter(
            orders__order_date__year=year,
            orders__order_date__month=month,
            orders__status__in=['confirmed', 'completed']
        ).distinct()
        
        summaries_created = 0
        
        for user in users_with_orders:
            # Get orders for the month
            monthly_orders = Order.objects.filter(
                user=user,
                order_date__year=year,
                order_date__month=month,
                status__in=['confirmed', 'completed']
            )
            
            # Calculate statistics
            total_orders = monthly_orders.count()
            total_items = monthly_orders.aggregate(Sum('total_items'))['total_items__sum'] or 0
            
            # Get item breakdown
            monthly_items = OrderItem.objects.filter(
                order__user=user,
                order__order_date__year=year,
                order__order_date__month=month,
                order__status__in=['confirmed', 'completed']
            ).values('item_name').annotate(
                total_quantity=Sum('quantity'),
                order_count=Count('order', distinct=True)
            )
            
            # Build summary data
            summary_data = {
                'items': {
                    item['item_name']: {
                        'quantity': item['total_quantity'],
                        'orders': item['order_count']
                    }
                    for item in monthly_items
                }
            }
            
            # Create or update summary
            summary, created = OrderSummary.objects.update_or_create(
                user=user,
                year=year,
                month=month,
                defaults={
                    'summary_data': summary_data,
                    'total_orders': total_orders,
                    'total_items': total_items,
                    'unique_items_ordered': len(summary_data['items'])
                }
            )
            
            summaries_created += 1
        
        logger.info(f"Generated {summaries_created} monthly summaries for {year}-{month:02d}")
        return f"Generated {summaries_created} summaries"
        
    except Exception as exc:
        logger.error(f"Failed to generate monthly summaries for {year}-{month}: {exc}")
        return f"Error: {exc}"


@shared_task(bind=True)
def finalize_daily_menu_reports(self):
    """
    Finalize reports for menus whose cutoff time has passed.
    Runs every 15 minutes to check for menus to finalize.
    """
    try:
        from .models import DailyMenu, DailyOrderReport
        
        now = timezone.now()
        today = now.date()
        current_time = now.time()
        
        # Find menus whose cutoff time has passed
        menus_to_finalize = DailyMenu.objects.filter(
            date=today,
            status='published',
            cutoff_time__lt=current_time,
            order_report__is_finalized=False
        )
        
        finalized_count = 0
        for menu in menus_to_finalize:
            try:
                report = menu.order_report
                report.finalize_report()
                finalized_count += 1
                
                # Send notification to kitchen/admin about finalized report
                send_kitchen_notification.delay(menu.id)
                
            except DailyOrderReport.DoesNotExist:
                # Create and finalize report
                generate_daily_order_report.delay(menu.id)
        
        logger.info(f"Finalized {finalized_count} menu reports")
        return f"Finalized {finalized_count} reports"
        
    except Exception as exc:
        logger.error(f"Failed to finalize reports: {exc}")
        return f"Error: {exc}"


@shared_task(bind=True)
def send_kitchen_notification(self, daily_menu_id):
    """
    Send notification to kitchen staff about finalized orders.
    In production, this would send email/SMS to kitchen staff.
    """
    try:
        from .models import DailyMenu
        
        daily_menu = DailyMenu.objects.get(id=daily_menu_id)
        report = daily_menu.order_report
        
        # In production, implement actual notification logic
        # For now, just log the notification
        logger.info(f"Kitchen notification: Menu for {daily_menu.date} finalized")
        logger.info(f"Total orders: {report.total_orders}")
        logger.info(f"Total items: {report.total_items}")
        
        return f"Notification sent for {daily_menu.date}"
        
    except Exception as exc:
        logger.error(f"Failed to send kitchen notification for menu {daily_menu_id}: {exc}")
        return f"Error: {exc}"


@shared_task(bind=True)
def cleanup_cancelled_orders(self):
    """
    Cleanup old cancelled orders and orphaned data.
    Runs daily to maintain database performance.
    """
    try:
        from .models import Order
        
        # Delete cancelled orders older than 90 days
        ninety_days_ago = timezone.now().date() - timedelta(days=90)
        
        deleted_count, _ = Order.objects.filter(
            status='cancelled',
            order_date__lt=ninety_days_ago
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old cancelled orders")
        return f"Cleaned up {deleted_count} orders"
        
    except Exception as exc:
        logger.error(f"Failed to cleanup cancelled orders: {exc}")
        return f"Error: {exc}"