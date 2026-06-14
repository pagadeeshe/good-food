from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Q, Count, Sum
from django.http import Http404
from django.utils import timezone
from django.core.cache import cache

from apps.authentication.permissions import IsAdminUser, IsOwnerOrAdmin
from .models import User, UserProfile
from .serializers import (
    UserListSerializer,
    UserDetailSerializer,
    UserCreateSerializer,
    UserUpdateSerializer,
    UserProfileUpdateSerializer,
    UserProfileDetailSerializer,
    BulkUserActionSerializer
)


class UserListCreateView(generics.ListCreateAPIView):
    """
    List all users or create new user (admin only).
    
    GET: List all users with search and filtering
    POST: Create new user (admin only)
    """
    serializer_class = UserListSerializer
    permission_classes = [IsAdminUser]
    
    def get_queryset(self):
        queryset = User.objects.select_related('profile').prefetch_related('orders')
        
        # Search functionality
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(employee_id__icontains=search)
            )
        
        # Filter by role
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(role=role)
        
        # Filter by active status
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        
        return queryset.order_by('-date_joined')
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return UserListSerializer


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieve, update or delete a user (admin only).
    """
    queryset = User.objects.select_related('profile')
    serializer_class = UserDetailSerializer
    permission_classes = [IsAdminUser]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserUpdateSerializer
        return UserDetailSerializer


class CurrentUserView(APIView):
    """
    Get or update current user's profile.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get current user profile."""
        cache_key = f"user_profile_{request.user.id}"
        
        # Try to get from cache first
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)
        
        serializer = UserDetailSerializer(request.user)
        data = serializer.data
        
        # Cache for 5 minutes
        cache.set(cache_key, data, 300)
        
        return Response(data)
    
    def patch(self, request):
        """Update current user profile."""
        serializer = UserProfileUpdateSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            
            # Clear cache
            cache_key = f"user_profile_{request.user.id}"
            cache.delete(cache_key)
            
            return Response(UserDetailSerializer(request.user).data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update user profile details.
    """
    serializer_class = UserProfileDetailSerializer
    permission_classes = [IsOwnerOrAdmin]
    
    def get_object(self):
        user_id = self.kwargs.get('user_id', self.request.user.id)
        try:
            user = User.objects.get(id=user_id)
            profile, created = UserProfile.objects.get_or_create(user=user)
            return profile
        except User.DoesNotExist:
            raise Http404("User not found")


class BulkUserActionView(APIView):
    """
    Perform bulk actions on users (admin only).
    """
    permission_classes = [IsAdminUser]
    
    def post(self, request):
        serializer = BulkUserActionSerializer(data=request.data)
        
        if serializer.is_valid():
            user_ids = serializer.validated_data['user_ids']
            action = serializer.validated_data['action']
            
            users = User.objects.filter(id__in=user_ids)
            updated_count = 0
            
            if action == 'activate':
                updated_count = users.update(is_active=True)
            elif action == 'deactivate':
                updated_count = users.update(is_active=False)
            elif action == 'promote_to_admin':
                updated_count = users.update(role='admin')
            elif action == 'demote_to_user':
                updated_count = users.update(role='user')
            
            return Response({
                'message': f'Successfully performed {action} on {updated_count} users.',
                'updated_count': updated_count
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def user_statistics(request):
    """
    Get user statistics for admin dashboard.
    """
    cache_key = "user_statistics"
    
    # Try cache first
    cached_stats = cache.get(cache_key)
    if cached_stats:
        return Response(cached_stats)
    
    # Calculate statistics
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    admin_users = User.objects.filter(role='admin').count()
    
    # Recent registrations (last 30 days)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    recent_registrations = User.objects.filter(date_joined__gte=thirty_days_ago).count()
    
    # Users with orders this month
    current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    users_with_orders = User.objects.filter(
        orders__order_date__gte=current_month,
        orders__status__in=['confirmed', 'completed']
    ).distinct().count()
    
    stats = {
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': total_users - active_users,
        'admin_users': admin_users,
        'regular_users': total_users - admin_users,
        'recent_registrations': recent_registrations,
        'users_with_orders_this_month': users_with_orders,
        'last_updated': timezone.now()
    }
    
    # Cache for 10 minutes
    cache.set(cache_key, stats, 600)
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def inactive_users(request):
    """
    Get list of inactive users (no orders in last 30 days).
    """
    thirty_days_ago = timezone.now().date() - timezone.timedelta(days=30)
    
    inactive_users = User.objects.filter(
        is_active=True,
        role='user'
    ).exclude(
        orders__order_date__gte=thirty_days_ago,
        orders__status__in=['confirmed', 'completed']
    ).select_related('profile')
    
    # Get last order date for each user
    users_data = []
    for user in inactive_users:
        last_order = user.orders.filter(
            status__in=['confirmed', 'completed']
        ).order_by('-order_date').first()
        
        users_data.append({
            'id': user.id,
            'employee_id': user.employee_id,
            'full_name': user.get_full_name(),
            'email': user.email,
            'last_order_date': last_order.order_date if last_order else None,
            'days_inactive': (timezone.now().date() - last_order.order_date).days if last_order else None,
            'total_orders': user.orders.filter(status__in=['confirmed', 'completed']).count()
        })
    
    return Response({
        'count': len(users_data),
        'users': users_data
    })


@api_view(['GET'])
@permission_classes([IsAdminUser])
def top_users(request):
    """
    Get top users by order count.
    """
    limit = int(request.query_params.get('limit', 10))
    
    # Get users with most orders
    top_users = User.objects.annotate(
        order_count=Count('orders', filter=Q(orders__status__in=['confirmed', 'completed'])),
        total_items=Sum('orders__total_items', filter=Q(orders__status__in=['confirmed', 'completed']))
    ).filter(order_count__gt=0).order_by('-order_count')[:limit]
    
    users_data = []
    for user in top_users:
        users_data.append({
            'id': user.id,
            'employee_id': user.employee_id,
            'full_name': user.get_full_name(),
            'email': user.email,
            'total_orders': user.order_count,
            'total_items': user.total_items or 0,
            'average_items_per_order': (user.total_items or 0) / user.order_count if user.order_count > 0 else 0
        })
    
    return Response({
        'count': len(users_data),
        'users': users_data
    })