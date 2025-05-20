from rest_framework import permissions

class IsOwnerOrReadOnlyAndGetPost(permissions.BasePermission):
    def has_permission(self, request,view):
        print("Request user in has_permission:", request.user)
        return True
    
    def has_object_permission(self, request, view, obj):
        print("Request user in has_object_permission:", request.user)
        print("Object user:", obj)
        if request.method in permissions.SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            return request.user.id == obj.id
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