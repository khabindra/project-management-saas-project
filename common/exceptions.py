from rest_framework.exceptions import APIException
from rest_framework import status


class TenantNotFoundError(APIException):
    """
    Raised when tenant is not found in request.
    """
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Tenant ID is required. Please provide X-Tenant-ID header.'
    default_code = 'tenant_not_found'


class MembershipRequiredError(APIException):
    """
    Raised when user is not a member of the tenant.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You are not a member of this tenant.'
    default_code = 'membership_required'


class RolePermissionError(APIException):
    """
    Raised when user doesn't have required role.
    """
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = 'You do not have permission to perform this action.'
    default_code = 'role_permission_error'