from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if hasattr(obj, "author") and hasattr(obj.author, "user"):
            return obj.author.user == request.user
        if hasattr(obj, "user"):
            return obj.user == request.user
        return False
