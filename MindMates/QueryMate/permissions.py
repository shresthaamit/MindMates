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
    """
    Custom permission to only allow owners of a review to edit or delete it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so GET, HEAD or OPTIONS requests are allowed.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the review
        return obj.user == request.user