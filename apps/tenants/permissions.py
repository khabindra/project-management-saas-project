from rest_framework.permissions import BasePermission
from common.exceptions import TenantNotFoundError
from .models import Membership


class IsValidTenant(BasePermission):
    """
    Validates that a tenant is present on the request and caches the
    requesting user's membership for downstream permission classes.

    MUST appear AFTER IsAuthenticated in permission_classes.
    """
    def has_permission(self, request, view):
        if not getattr(request, 'tenant', None):
            raise TenantNotFoundError()

        # OPTIMIZATION: Fetch membership once and attach to request
        # so IsTenantMember/Owner/Admin don't hit the DB again.
        request.membership = (
            Membership.objects
            .filter(
                user_id=request.user.pk,
                tenant_id=request.tenant.pk,
                is_active=True
            )
            .first()
        )
        return True


class IsTenantMember(BasePermission):
    message = "You are not a member of this tenant."

    def has_permission(self, request, view):
        return getattr(request, 'membership', None) is not None


class IsTenantOwner(BasePermission):
    message = "Only the tenant owner can perform this action."

    def has_permission(self, request, view):
        membership = getattr(request, 'membership', None)
        return bool(membership and membership.is_owner)


class IsTenantAdmin(BasePermission):
    message = "Only tenant admins or owners can perform this action."

    def has_permission(self, request, view):
        membership = getattr(request, 'membership', None)
        return bool(membership and membership.is_admin)