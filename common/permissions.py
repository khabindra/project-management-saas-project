from rest_framework.permissions import BasePermission


class IsOwnerOrAdmin(BasePermission):
    """
    Only allow owners or admins to access.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.owner == request.user