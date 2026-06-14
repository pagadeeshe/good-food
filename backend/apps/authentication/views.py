from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import logout
from django.utils.decorators import method_decorator
from django_ratelimit.decorators import ratelimit
from django.utils import timezone

from .serializers import (
    CustomTokenObtainPairSerializer,
    LoginSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer,
    PasswordChangeSerializer,
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer
)


@method_decorator(ratelimit(key='ip', rate='5/m', method='POST'), name='post')
class LoginView(TokenObtainPairView):
    """
    Login view with JWT tokens and rate limiting.
    Rate limited to 5 attempts per minute per IP.
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Log successful login
            from django.contrib.admin.models import LogEntry, ADDITION
            from django.contrib.contenttypes.models import ContentType
            
            user_data = response.data.get('user', {})
            user_id = user_data.get('id')
            
            if user_id:
                try:
                    LogEntry.objects.create(
                        user_id=user_id,
                        content_type=ContentType.objects.get_for_model(request.user.__class__),
                        object_id=user_id,
                        object_repr=f"Login: {user_data.get('email')}",
                        action_flag=ADDITION,
                        change_message="User logged in"
                    )
                except Exception:
                    pass  # Don't fail login if logging fails
        
        return response


class LogoutView(APIView):
    """
    Logout view that blacklists the refresh token.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            logout(request)
            
            return Response(
                {'message': 'Successfully logged out.'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': 'Invalid token or logout failed.'},
                status=status.HTTP_400_BAD_REQUEST
            )


@method_decorator(ratelimit(key='ip', rate='3/h', method='POST'), name='post')
class RegisterView(APIView):
    """
    User registration view.
    Rate limited to 3 registrations per hour per IP.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Generate tokens for immediate login
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'message': 'User registered successfully.',
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    """
    User profile view for viewing and updating profile.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get current user profile."""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """Update current user profile."""
        serializer = UserProfileSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(ratelimit(key='user', rate='3/h', method='POST'), name='post')
class PasswordChangeView(APIView):
    """
    Password change view.
    Rate limited to 3 attempts per hour per user.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Password changed successfully.'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(ratelimit(key='ip', rate='3/h', method='POST'), name='post')
class PasswordResetRequestView(APIView):
    """
    Password reset request view.
    Rate limited to 3 requests per hour per IP.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        
        if serializer.is_valid():
            # In a real implementation, send email with reset link
            # For now, just return success
            return Response({
                'message': 'Password reset instructions sent to your email.'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    """
    Password reset confirmation view.
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        
        if serializer.is_valid():
            # In a real implementation, validate token and reset password
            # For now, just return success
            return Response({
                'message': 'Password reset successfully.'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_permissions(request):
    """
    Get current user permissions and role information.
    """
    user = request.user
    
    permissions_data = {
        'user_id': user.id,
        'email': user.email,
        'employee_id': user.employee_id,
        'role': user.role,
        'is_admin': user.is_admin,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'permissions': {
            'can_manage_users': user.is_admin or user.is_staff,
            'can_manage_menus': user.is_admin or user.is_staff,
            'can_view_reports': user.is_admin or user.is_staff,
            'can_place_orders': user.is_active,
            'can_modify_orders': user.is_active,
        }
    }
    
    return Response(permissions_data)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def refresh_user_profile(request):
    """
    Refresh user profile data from database.
    Useful after profile updates.
    """
    user = request.user
    user.refresh_from_db()
    
    return Response({
        'user': UserProfileSerializer(user).data,
        'timestamp': timezone.now()
    })


class TokenVerifyView(APIView):
    """
    Verify JWT token validity.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        return Response({
            'valid': True,
            'user': UserProfileSerializer(request.user).data,
            'timestamp': timezone.now()
        })