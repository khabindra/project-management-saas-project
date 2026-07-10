import uuid
from django.core.cache import cache
from .models import Tenant

TENANT_CACHE_TIMEOUT = 300  # 5 minutes


def get_tenant_cache_key(tenant_id: str) -> str:
    return f'tenant:{tenant_id}'


def invalidate_tenant_cache(tenant_id) -> None:
    """Call this whenever a tenant is modified or deactivated."""
    cache.delete(get_tenant_cache_key(str(tenant_id)))


class TenantMiddleware:
    """
    Middleware to extract tenant from request headers
    and attach it to the request object.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tenant_id = request.headers.get('X-Tenant-ID')
        request.tenant = None

        if tenant_id:
            # Validate UUID format BEFORE cache/DB access
            try:
                tenant_uuid = uuid.UUID(tenant_id)
            except (ValueError, AttributeError):
                # SECURITY FIX: Don't silently continue. 
                # Mark the request as having an invalid tenant format.
                request.tenant_id_invalid_format = True
                return self.get_response(request)

            cache_key = get_tenant_cache_key(str(tenant_uuid))
            tenant = cache.get(cache_key)

            if tenant is None:
                try:
                    tenant = Tenant.objects.get(
                        id=tenant_uuid,
                        is_active=True
                    )
                    cache.set(cache_key, tenant, timeout=TENANT_CACHE_TIMEOUT)
                except Tenant.DoesNotExist:
                    tenant = None

            request.tenant = tenant

        return self.get_response(request)