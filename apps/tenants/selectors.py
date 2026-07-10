from django.db import models
from .models import Tenant, Membership


def get_tenants_for_user(user) -> models.QuerySet:
    """
    Get all tenants where user is an active member.
    """
    return Tenant.objects.filter(
        memberships__user=user,
        memberships__is_active=True
    ).distinct()


def get_tenant_by_slug(slug: str) -> Tenant | None:
    try:
        return Tenant.objects.get(slug=slug, is_active=True)
    except Tenant.DoesNotExist:
        return None


def get_tenant_by_id(tenant_id: str) -> Tenant | None:
    try:
        return Tenant.objects.get(id=tenant_id, is_active=True)
    except (Tenant.DoesNotExist, ValueError):
        return None


def get_membership(user, tenant) -> Membership | None:
    try:
        return Membership.objects.get(user=user, tenant=tenant, is_active=True)
    except Membership.DoesNotExist:
        return None


def get_memberships_for_tenant(tenant) -> models.QuerySet:
    return Membership.objects.filter(
        tenant=tenant, is_active=True
    ).select_related('user')


def check_user_is_member(user, tenant) -> bool:
    return Membership.objects.filter(user=user, tenant=tenant, is_active=True).exists()


def check_user_has_role(user, tenant, roles: list) -> bool:
    return Membership.objects.filter(user=user, tenant=tenant, role__in=roles, is_active=True).exists()