from rest_framework.permissions import BasePermission


class CanManageTask(BasePermission):
    """
    Controls update and delete permissions.
    - GET/HEAD/OPTIONS: All members
    - PATCH/DELETE: Only OWNER or ADMIN
    """
    message = 'Only tenant owners or admins can modify or delete tasks.'

    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        membership = getattr(request, 'membership', None)
        if not membership:
            return False

        return membership.is_admin