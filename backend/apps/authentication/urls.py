from django.urls import path
from .views import (
    LoginView,
    LogoutView,
    RegisterView,
    ProfileView,
    PasswordChangeView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    TokenVerifyView,
    CookieTokenRefreshView,
    user_permissions,
    refresh_user_profile
)

app_name = 'authentication'

urlpatterns = [
    # Authentication
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    
    # JWT Token Management
    path('token/refresh/', CookieTokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # User Profile
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/refresh/', refresh_user_profile, name='profile_refresh'),
    path('permissions/', user_permissions, name='user_permissions'),
    
    # Password Management
    path('password/change/', PasswordChangeView.as_view(), name='password_change'),
    path('password/reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('password/reset/confirm/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
]