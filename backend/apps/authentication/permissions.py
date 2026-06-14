from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    Permission class for admin-only views.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_admin
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission class that allows access to owners of objects or admin users.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Admin users can access any object
        if request.user.is_admin:
            return True
        
        # Check if object has a user field and user owns it
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Check if object is the user itself
        if hasattr(obj, 'id') and hasattr(request.user, 'id'):
            return obj.id == request.user.id
        
        return False


class IsOwner(permissions.BasePermission):
    """
    Permission class that only allows access to owners of objects.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Check if object has a user field and user owns it
        if hasattr(obj, 'user'):
            return obj.user == request.user
        
        # Check if object is the user itself
        if hasattr(obj, 'id') and hasattr(request.user, 'id'):
            return obj.id == request.user.id
        
        return False


class CanPlaceOrder(permissions.BasePermission):
    """
    Permission class for order placement.
    Checks if user can place orders (active user with appropriate role).
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_active
        )


class CanManageMenus(permissions.BasePermission):
    """
    Permission class for menu management.
    Only admin users can create, update, or delete menus.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            # Anyone can view menus
            return request.user and request.user.is_authenticated
        
        # Only admins can modify menus
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_admin
        )


class CanViewReports(permissions.BasePermission):
    """
    Permission class for viewing reports.
    Only admin users can view reports.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_admin
        )


class ReadOnlyOrAdmin(permissions.BasePermission):
    """
    Permission class that allows read-only access to authenticated users
    and full access to admin users.
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return request.user.is_admin