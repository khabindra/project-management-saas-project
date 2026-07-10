from rest_framework.permissions import BasePermission


class IsProjectAdminOrReadOnly(BasePermission):
    """
    Permission class for project access.
    
    - READ operations (GET, HEAD, OPTIONS): Allowed for all tenant members
    - WRITE operations (POST, PATCH, PUT, DELETE): Allowed only for tenant OWNER or ADMIN
    
    Must be used AFTER IsValidTenant and IsTenantMember in permission_classes,
    because it relies on request.membership being set by IsValidTenant.
    
    Usage:
        permission_classes = [
            IsAuthenticated,        # User must be logged in
            IsValidTenant,          # Sets request.tenant and request.membership
            IsTenantMember,         # Verifies user is a member
            IsProjectAdminOrReadOnly,  # This class
        ]
    """
    message = 'Only tenant owners or admins can perform this action.'

    def has_permission(self, request, view):
        # Safe methods (GET, HEAD, OPTIONS) are allowed for all members
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True

        # Write methods require OWNER or ADMIN role
        membership = getattr(request, 'membership', None)
        
        if not membership:
            return False
        
        # is_admin property returns True for both OWNER and ADMIN roles
        return membership.is_admin