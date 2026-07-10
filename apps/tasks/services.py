from django.db import transaction
from typing import Optional
from apps.tenants.models import Tenant
from apps.projects.models import Project
from apps.accounts.models import User
from .models import Task


@transaction.atomic
def create_task(
    *, 
    tenant: 'Tenant', 
    project: 'Project', 
    user: 'User', 
    title: str, 
    description: str = "", 
    assignee: Optional['User'] = None
) -> Task:
    """
    Create a new task.
    Expects a pre-validated User object for assignee (or None).
    """
    return Task.objects.create(
        tenant=tenant,
        project=project,
        created_by=user,
        title=title,
        description=description,
        assignee=assignee
    )


@transaction.atomic
def update_task(*, task: Task, **kwargs) -> Task:
    """
    Update task details dynamically.
    Expects 'assignee' key with a pre-validated User object (or None).
    """
    update_fields = ['updated_at']

    if 'title' in kwargs:
        task.title = kwargs['title']
        update_fields.append('title')

    if 'description' in kwargs:
        task.description = kwargs['description']
        update_fields.append('description')

    if 'status' in kwargs:
        task.status = kwargs['status']
        update_fields.append('status')

    # RELIABILITY: Directly assign the User object passed from the view.
    # This removes the need for an extra DB query inside the service layer.
    if 'assignee' in kwargs:
        task.assignee = kwargs['assignee']
        update_fields.append('assignee')

    if len(update_fields) == 1:
        raise ValueError('No valid fields provided for update.')

    task.save(update_fields=update_fields)
    return task


@transaction.atomic
def delete_task(*, task: Task) -> None:
    """
    Soft delete a task.
    """
    task.is_active = False
    task.save(update_fields=['is_active', 'updated_at'])