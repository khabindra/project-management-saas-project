from django.db import transaction, IntegrityError
from django.utils.text import slugify

from .models import Tenant, Membership
from .middleware import invalidate_tenant_cache
from apps.accounts.selectors import get_user_by_email

_MAX_SLUG_RETRIES = 20


@transaction.atomic
def create_tenant(*, name: str, owner) -> Tenant:
    """
    Create a new tenant with a unique slug and make the creator the owner.
    Uses nested savepoints so IntegrityError doesn't poison the outer
    transaction (critical for PostgreSQL).
    """
    base_slug = slugify(name)
    slug = base_slug

    for counter in range(1, _MAX_SLUG_RETRIES + 1):
        try:
            with transaction.atomic():
                tenant = Tenant.objects.create(
                    name=name,
                    slug=slug,
                    owner=owner
                )
            break
        except IntegrityError:
            slug = f'{base_slug}-{counter}'
            continue
    else:
        raise RuntimeError(
            f'Could not create tenant "{name}" after {_MAX_SLUG_RETRIES} attempts.'
        )

    Membership.objects.create(
        user=owner,
        tenant=tenant,
        role=Membership.Role.OWNER
    )
    return tenant


@transaction.atomic
def update_tenant(*, tenant: Tenant, name: str) -> Tenant:
    """
    Update tenant name and regenerate slug if changed.
    Uses single .save() with savepoint retry.
    """
    if tenant.name == name:
        return tenant

    base_slug = slugify(name)
    slug = base_slug

    for counter in range(1, _MAX_SLUG_RETRIES + 1):
        try:
            with transaction.atomic():
                tenant.name = name
                tenant.slug = slug
                tenant.save(update_fields=['name', 'slug', 'updated_at'])
        except IntegrityError:
            slug = f'{base_slug}-{counter}'
            continue
        break
    else:
        raise RuntimeError(
            f'Could not update tenant "{name}" after {_MAX_SLUG_RETRIES} attempts.'
        )

    invalidate_tenant_cache(tenant.pk)
    return tenant


@transaction.atomic
def delete_tenant(*, tenant) -> None:
    tenant.is_active = False
    tenant.save(update_fields=['is_active', 'updated_at'])
    invalidate_tenant_cache(tenant.pk)


@transaction.atomic
def invite_member(*, tenant: Tenant, email: str, role: str) -> Membership:
    """
    Invite a user by email. Reactivates if previously removed.
    """
    user = get_user_by_email(email)
    if not user:
        raise ValueError('User with this email does not exist.')

    if Membership.objects.filter(user=user, tenant=tenant, is_active=True).exists():
        raise ValueError('User is already an active member of this tenant.')

    membership, created = Membership.objects.update_or_create(
        user=user,
        tenant=tenant,
        defaults={'role': role, 'is_active': True},
    )
    return membership


@transaction.atomic
def update_member_role(*, membership, role: str) -> Membership:
    """
    Update a member's role (ADMIN or MEMBER only).
    For ownership transfer, use transfer_ownership() instead.
    """
    membership.role = role
    membership.save(update_fields=['role', 'updated_at'])
    return membership


@transaction.atomic
def transfer_ownership(*, tenant: Tenant, current_owner_membership: Membership, target_membership: Membership) -> Membership:
    """
    Transfer ownership from current owner to target member.
    
    This is atomic:
    1. Target member becomes OWNER
    2. Current owner becomes ADMIN
    3. Tenant.owner field is updated
    
    After this, the former owner can leave the tenant as an ADMIN.
    """
    # Validate target is not already owner
    if target_membership.role == Membership.Role.OWNER:
        raise ValueError('Target user is already the owner.')
    
    # Validate target is an active member
    if not target_membership.is_active:
        raise ValueError('Target user is not an active member.')
    
    # Validate current user is actually the owner
    if current_owner_membership.role != Membership.Role.OWNER:
        raise ValueError('Only the owner can transfer ownership.')
    
    # Prevent self-transfer
    if current_owner_membership.user_id == target_membership.user_id:
        raise ValueError('Cannot transfer ownership to yourself.')
    
    # Step 1: Demote current owner to ADMIN
    current_owner_membership.role = Membership.Role.ADMIN
    current_owner_membership.save(update_fields=['role', 'updated_at'])
    
    # Step 2: Promote target to OWNER
    target_membership.role = Membership.Role.OWNER
    target_membership.save(update_fields=['role', 'updated_at'])
    
    # Step 3: Update tenant.owner field
    tenant.owner = target_membership.user
    tenant.save(update_fields=['owner', 'updated_at'])
    
    # Step 4: Invalidate cache
    invalidate_tenant_cache(tenant.pk)
    
    return target_membership


@transaction.atomic
def remove_member(*, membership) -> None:
    membership.is_active = False
    membership.save(update_fields=['is_active', 'updated_at'])


@transaction.atomic
def leave_tenant(*, membership: Membership) -> None:
    """
    Leave a tenant. Accepts pre-fetched membership to avoid redundant query.
    Caller should use select_for_update() to prevent TOCTOU race.
    """
    if membership.role == Membership.Role.OWNER:
        raise ValueError('Owner cannot leave. Transfer ownership first.')
    membership.is_active = False
    membership.save(update_fields=['is_active', 'updated_at'])