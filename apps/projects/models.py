from django.db import models
from django.conf import settings
from common.models import TimeStampedModel
from apps.tenants.models import Tenant


class Project(TimeStampedModel):
    """
    Project model. Every project belongs to a Tenant.
    SaaS Rule #1: Always include tenant ForeignKey.
    """
    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='projects',
        db_index=True,
    )
    name = models.CharField(max_length=255)  # Original case preserved for display
    name_lower = models.CharField(max_length=255, db_index=True)  # Normalized for uniqueness
    description = models.TextField(blank=True, default='')
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_projects'
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'projects'
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
        ordering = ['-created_at']
        constraints = [
            # Use name_lower for case-insensitive, space-insensitive uniqueness
            models.UniqueConstraint(
                fields=['tenant', 'name_lower'],
                name='unique_project_name_per_tenant',
                condition=models.Q(is_active=True),
            )
        ]

    def __str__(self):
        return f"[{self.tenant.slug}] {self.name}"