from django.db import models
from django.conf import settings
from common.models import TimeStampedModel
from apps.tenants.models import Tenant
from apps.projects.models import Project


class Task(TimeStampedModel):
    """
    Task model. Belongs to a Tenant AND a Project.
    """
    class Status(models.TextChoices):
        TODO = 'TODO', 'To Do'
        IN_PROGRESS = 'IN_PROGRESS', 'In Progress'
        DONE = 'DONE', 'Done'

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.CASCADE,
        related_name='tasks',
        db_index=True
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='tasks',
        db_index=True
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    status = models.CharField(
        max_length=30,
        choices=Status.choices,
        default=Status.TODO,
        db_index=True
    )
    assignee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='assigned_tasks'
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tasks'
    )
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        db_table = 'tasks'
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['-created_at']
        
        # SCALABILITY: Optimized partial indexes for Postgres
        # Note: We removed 'is_active' from fields because it's already in the condition
        indexes = [
            models.Index(
                fields=['tenant', 'project'],
                name='task_tenant_project_idx',
                condition=models.Q(is_active=True),
            ),
            models.Index(
                fields=['tenant', 'assignee'],
                name='task_tenant_assignee_idx',
                condition=models.Q(is_active=True),
            ),
            models.Index(
                fields=['tenant', 'status'],
                name='task_tenant_status_idx',
                condition=models.Q(is_active=True),
            ),
        ]

    def __str__(self):
        return f"[{self.project.name}] {self.title}"