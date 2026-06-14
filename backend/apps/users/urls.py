from django.urls import path
from .views import (
    UserListCreateView,
    UserDetailView,
    CurrentUserView,
    UserProfileView,
    BulkUserActionView,
    user_statistics,
    inactive_users,
    top_users
)

app_name = 'users'

urlpatterns = [
    # User management (admin only)
    path('', UserListCreateView.as_view(), name='user_list_create'),
    path('<int:pk>/', UserDetailView.as_view(), name='user_detail'),
    path('bulk-action/', BulkUserActionView.as_view(), name='bulk_user_action'),
    
    # Current user
    path('me/', CurrentUserView.as_view(), name='current_user'),
    path('me/profile/', UserProfileView.as_view(), name='current_user_profile'),
    
    # User profiles
    path('<int:user_id>/profile/', UserProfileView.as_view(), name='user_profile'),
    
    # Statistics and analytics (admin only)
    path('statistics/', user_statistics, name='user_statistics'),
    path('inactive/', inactive_users, name='inactive_users'),
    path('top/', top_users, name='top_users'),
]