from django.conf import settings
from django.db import models
from common.models import TimeStampedModel


class Tenant(TimeStampedModel):
    """
    Tenant (Workspace) model.
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=255)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_tenants',
        db_index=True,
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'tenants'
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
        ordering = ['-created_at']

    def __str__(self):
        return self.name


class Membership(TimeStampedModel):
    """
    Membership model - connects users to tenants with roles.
    """
    class Role(models.TextChoices):
        OWNER = 'OWNER', 'Owner'
        ADMIN = 'ADMIN', 'Admin'
        MEMBER = 'MEMBER', 'Member'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    role = models.CharField(
        max_length=30,
        choices=Role.choices,
        default=Role.MEMBER,
        db_index=True
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'memberships'
        verbose_name = 'Membership'
        verbose_name_plural = 'Memberships'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'tenant'],
                name='unique_user_tenant_membership'
            )
        ]
        indexes = [
            models.Index(
                fields=['user', 'tenant'],
                name='member_usr_tnnt_act_idx',
                condition=models.Q(is_active=True),
            ),
            models.Index(
                fields=['tenant'],
                name='membership_tenant_active_idx',
                condition=models.Q(is_active=True),
            ),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.tenant.name} ({self.role})"

    @property
    def is_owner(self):
        return self.role == self.Role.OWNER

    @property
    def is_admin(self):
        return self.role in [self.Role.OWNER, self.Role.ADMIN]