from rest_framework import permissions

class IsOwnerOrReadOnlyAndGetPost(permissions.BasePermission):
    def has_permission(self, request,view):
        return True
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user.is_anonymous:
            return request.user == obj
        
        return False
    
    
class IsProfileUserOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return True
    
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if not request.user.is_anonymous:
            return request.user.userprofile == obj
        
        return False