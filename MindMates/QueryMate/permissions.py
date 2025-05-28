from rest_framework import permissions

class IsAdminOrStaffOtherReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method  in permissions.SAFE_METHODS:
            return True
        return request.user.is_staff or request.user.is_superuser
    
    
class IsAuthenticated(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
class IsOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user == obj.user
    
    
class IsReviewOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # Allow read-only for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        # Allow write only if user owns the object
        return obj.user == request.user