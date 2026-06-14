from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Count, Sum
from django.utils import timezone
from django.core.cache import cache
from django.shortcuts import get_object_or_404

from apps.authentication.permissions import IsAdminUser, CanManageMenus, ReadOnlyOrAdmin
from .models import WeeklyMenu, DailyMenu, MenuItem, MenuTemplate, MenuTemplateItem
from .serializers import (
    WeeklyMenuSerializer, WeeklyMenuCreateSerializer,
    DailyMenuSerializer, DailyMenuCreateSerializer, TodayMenuSerializer,
    MenuItemSerializer, MenuItemCreateSerializer,
    MenuTemplateSerializer, MenuTemplateCreateSerializer,
    MenuItemBulkUpdateSerializer, DailyMenuFromTemplateSerializer,
    MenuStatisticsSerializer
)


class TodayMenuView(APIView):
    """
    Get today's menu for users to place orders.
    Heavily cached for performance with 10,000+ users.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        today = timezone.now().date()
        cache_key = f"today_menu_{today}"
        
        # Try cache first (5 minute TTL)
        cached_menu = cache.get(cache_key)
        if cached_menu:
            return Response(cached_menu)
        
        try:
            daily_menu = DailyMenu.objects.select_related('weekly_menu').prefetch_related(
                'menu_items'
            ).get(date=today, status='published')
            
            serializer = TodayMenuSerializer(daily_menu)
            data = serializer.data
            
            # Cache for 5 minutes
            cache.set(cache_key, data, 300)
            
            return Response(data)
            
        except DailyMenu.DoesNotExist:
            return Response(
                {'error': 'No menu available for today'},
                status=status.HTTP_404_NOT_FOUND
            )


class DailyMenuListView(generics.ListCreateAPIView):
    """
    List all daily menus or create new daily menu (admin only).
    """
    serializer_class = DailyMenuSerializer
    permission_classes = [CanManageMenus]
    
    def get_queryset(self):
        queryset = DailyMenu.objects.select_related('weekly_menu', 'created_by').prefetch_related('menu_items')
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-date')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DailyMenuCreateSerializer
        return DailyMenuSerializer


class DailyMenuDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a daily menu (admin only).
    """
    queryset = DailyMenu.objects.select_related('weekly_menu', 'created_by').prefetch_related('menu_items')
    serializer_class = DailyMenuSerializer
    permission_classes = [CanManageMenus]
    
    def perform_update(self, serializer):
        # Clear cache when menu is updated
        menu = serializer.save()
        cache_keys = [
            f"today_menu_{menu.date}",
            f"daily_menu_{menu.id}",
        ]
        cache.delete_many(cache_keys)


class MenuItemListCreateView(generics.ListCreateAPIView):
    """
    List menu items for a daily menu or add new items (admin only).
    """
    serializer_class = MenuItemSerializer
    permission_classes = [ReadOnlyOrAdmin]
    
    def get_queryset(self):
        daily_menu_id = self.kwargs['daily_menu_id']
        return MenuItem.objects.filter(daily_menu_id=daily_menu_id).order_by('sort_order', 'name')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MenuItemCreateSerializer
        return MenuItemSerializer
    
    def perform_create(self, serializer):
        daily_menu_id = self.kwargs['daily_menu_id']
        daily_menu = get_object_or_404(DailyMenu, id=daily_menu_id)
        serializer.save(daily_menu=daily_menu)
        
        # Clear cache
        cache_keys = [
            f"today_menu_{daily_menu.date}",
            f"daily_menu_{daily_menu.id}",
        ]
        cache.delete_many(cache_keys)


class MenuItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a menu item (admin only).
    """
    queryset = MenuItem.objects.select_related('daily_menu')
    serializer_class = MenuItemSerializer
    permission_classes = [CanManageMenus]
    
    def perform_update(self, serializer):
        item = serializer.save()
        # Clear cache
        cache_keys = [
            f"today_menu_{item.daily_menu.date}",
            f"daily_menu_{item.daily_menu.id}",
        ]
        cache.delete_many(cache_keys)


class WeeklyMenuListView(generics.ListCreateAPIView):
    """
    List all weekly menus or create new weekly menu (admin only).
    """
    serializer_class = WeeklyMenuSerializer
    permission_classes = [ReadOnlyOrAdmin]
    
    def get_queryset(self):
        queryset = WeeklyMenu.objects.select_related('created_by').prefetch_related('daily_menus')
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('-week_start_date')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return WeeklyMenuCreateSerializer
        return WeeklyMenuSerializer


class WeeklyMenuDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a weekly menu (admin only).
    """
    queryset = WeeklyMenu.objects.select_related('created_by').prefetch_related('daily_menus')
    serializer_class = WeeklyMenuSerializer
    permission_classes = [ReadOnlyOrAdmin]


class MenuTemplateListView(generics.ListCreateAPIView):
    """
    List all menu templates or create new template (admin only).
    """
    serializer_class = MenuTemplateSerializer
    permission_classes = [ReadOnlyOrAdmin]
    
    def get_queryset(self):
        queryset = MenuTemplate.objects.select_related('created_by').prefetch_related('template_items')
        
        # Filter by weekday
        weekday = self.request.query_params.get('weekday')
        if weekday is not None:
            queryset = queryset.filter(weekday=weekday)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active')
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('weekday', 'name')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MenuTemplateCreateSerializer
        return MenuTemplateSerializer


class MenuTemplateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a menu template (admin only).
    """
    queryset = MenuTemplate.objects.select_related('created_by').prefetch_related('template_items')
    serializer_class = MenuTemplateSerializer
    permission_classes = [CanManageMenus]


class MenuItemBulkUpdateView(APIView):
    """
    Perform bulk operations on menu items (admin only).
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request, daily_menu_id):
        serializer = MenuItemBulkUpdateSerializer(data=request.data)
        
        if serializer.is_valid():
            item_ids = serializer.validated_data['item_ids']
            action = serializer.validated_data['action']
            max_quantity = serializer.validated_data.get('max_quantity')
            
            # Get items belonging to the daily menu
            items = MenuItem.objects.filter(
                id__in=item_ids,
                daily_menu_id=daily_menu_id
            )
            
            updated_count = 0
            
            if action == 'make_available':
                updated_count = items.update(is_available=True)
            elif action == 'make_unavailable':
                updated_count = items.update(is_available=False)
            elif action == 'update_quantity' and max_quantity:
                updated_count = items.update(max_quantity_per_user=max_quantity)
            
            # Clear cache
            daily_menu = get_object_or_404(DailyMenu, id=daily_menu_id)
            cache_keys = [
                f"today_menu_{daily_menu.date}",
                f"daily_menu_{daily_menu.id}",
            ]
            cache.delete_many(cache_keys)
            
            return Response({
                'message': f'Successfully updated {updated_count} items.',
                'updated_count': updated_count
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateMenuFromTemplateView(APIView):
    """
    Create daily menu from template (admin only).
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        serializer = DailyMenuFromTemplateSerializer(data=request.data)
        
        if serializer.is_valid():
            template_id = serializer.validated_data['template_id']
            date = serializer.validated_data['date']
            cutoff_time = serializer.validated_data.get('cutoff_time')
            description = serializer.validated_data.get('description', '')
            
            # Get template
            template = get_object_or_404(MenuTemplate, id=template_id, is_active=True)
            
            # Create daily menu
            daily_menu = DailyMenu.objects.create(
                date=date,
                cutoff_time=cutoff_time or template.weekday,  # You might want default cutoff times
                description=description or f"Menu from template: {template.name}",
                created_by=request.user
            )
            
            # Copy template items to menu items
            template_items = template.template_items.all()
            menu_items = []
            
            for template_item in template_items:
                menu_item = MenuItem(
                    daily_menu=daily_menu,
                    name=template_item.name,
                    description=template_item.description,
                    category=template_item.category,
                    max_quantity_per_user=template_item.max_quantity_per_user,
                    sort_order=template_item.sort_order
                )
                menu_items.append(menu_item)
            
            # Bulk create menu items
            MenuItem.objects.bulk_create(menu_items)
            
            # Update template usage count
            template.usage_count = F('usage_count') + 1
            template.save(update_fields=['usage_count'])
            
            # Return created menu
            daily_menu.refresh_from_db()
            return Response(
                DailyMenuSerializer(daily_menu).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def menu_statistics(request):
    """
    Get menu statistics for admin dashboard.
    """
    cache_key = "menu_statistics"
    
    # Try cache first
    cached_stats = cache.get(cache_key)
    if cached_stats:
        return Response(cached_stats)
    
    # Calculate statistics
    today = timezone.now().date()
    
    # Basic counts
    total_menus = DailyMenu.objects.count()
    published_menus = DailyMenu.objects.filter(status='published').count()
    draft_menus = DailyMenu.objects.filter(status='draft').count()
    total_items = MenuItem.objects.count()
    
    # Most popular items (last 30 days)
    thirty_days_ago = today - timezone.timedelta(days=30)
    popular_items = MenuItem.objects.filter(
        daily_menu__date__gte=thirty_days_ago
    ).annotate(
        total_orders=Sum('order_items__quantity')
    ).filter(total_orders__gt=0).order_by('-total_orders')[:10]
    
    most_popular_items = [
        {
            'name': item.name,
            'total_ordered': item.total_orders,
            'category': item.category
        }
        for item in popular_items
    ]
    
    # Recent menus
    recent_menus = DailyMenu.objects.select_related('created_by').order_by('-created_at')[:5]
    recent_menus_data = [
        {
            'id': menu.id,
            'date': menu.date,
            'status': menu.status,
            'total_orders': menu.total_orders,
            'created_by': menu.created_by.get_full_name()
        }
        for menu in recent_menus
    ]
    
    # Upcoming menus
    upcoming_menus = DailyMenu.objects.filter(
        date__gt=today
    ).order_by('date')[:5]
    
    upcoming_menus_data = [
        {
            'id': menu.id,
            'date': menu.date,
            'status': menu.status,
            'item_count': menu.menu_items.count()
        }
        for menu in upcoming_menus
    ]
    
    stats = {
        'total_menus': total_menus,
        'published_menus': published_menus,
        'draft_menus': draft_menus,
        'total_items': total_items,
        'most_popular_items': most_popular_items,
        'recent_menus': recent_menus_data,
        'upcoming_menus': upcoming_menus_data,
        'last_updated': timezone.now()
    }
    
    # Cache for 15 minutes
    cache.set(cache_key, stats, 900)
    
    return Response(stats)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def publish_menu(request, daily_menu_id):
    """
    Publish a daily menu.
    """
    daily_menu = get_object_or_404(DailyMenu, id=daily_menu_id)
    
    if daily_menu.status != 'draft':
        return Response(
            {'error': 'Only draft menus can be published.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Ensure menu has items
    if not daily_menu.menu_items.exists():
        return Response(
            {'error': 'Cannot publish menu without items.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    daily_menu.status = 'published'
    daily_menu.save(update_fields=['status'])
    
    # Clear cache
    cache_keys = [
        f"today_menu_{daily_menu.date}",
        f"daily_menu_{daily_menu.id}",
        "menu_statistics"
    ]
    cache.delete_many(cache_keys)
    
    return Response({
        'message': 'Menu published successfully.',
        'menu': DailyMenuSerializer(daily_menu).data
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def close_menu(request, daily_menu_id):
    """
    Close a daily menu (stop accepting orders).
    """
    daily_menu = get_object_or_404(DailyMenu, id=daily_menu_id)
    
    if daily_menu.status != 'published':
        return Response(
            {'error': 'Only published menus can be closed.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    daily_menu.status = 'closed'
    daily_menu.save(update_fields=['status'])
    
    # Trigger report generation
    from .tasks import generate_daily_order_report
    generate_daily_order_report.delay(daily_menu.id)
    
    # Clear cache
    cache_keys = [
        f"today_menu_{daily_menu.date}",
        f"daily_menu_{daily_menu.id}",
    ]
    cache.delete_many(cache_keys)
    
    return Response({
        'message': 'Menu closed successfully. Order report will be generated.',
        'menu': DailyMenuSerializer(daily_menu).data
    })