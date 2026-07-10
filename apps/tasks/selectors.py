from .models import Task


def get_tasks_for_project(tenant, project):
    """
    PERFORMANCE: Uses .only() to avoid loading massive 'description' 
    payloads into memory for list views.
    """
    return Task.objects.filter(
        tenant=tenant,
        project=project,
        is_active=True
    ).select_related(
        'assignee', 'project'
    ).only(
        'id', 'title', 'status', 'created_at',
        'project__name',
        'assignee__email', 'assignee__first_name', 'assignee__last_name'
    )


def get_my_tasks_for_tenant(tenant, user):
    """
    PERFORMANCE: Uses .only() to avoid loading 'description' 
    payloads into memory for list views.
    """
    return Task.objects.filter(
        tenant=tenant,
        assignee=user,
        is_active=True
    ).select_related(
        'assignee', 'project'
    ).only(
        'id', 'title', 'status', 'created_at',
        'project__name',
        'assignee__email', 'assignee__first_name', 'assignee__last_name'
    )


def get_task_detail_for_tenant(tenant, task_id) -> Task | None:
    """
    Full task detail with all related data. 
    No .only() here because we need everything including description.
    """
    try:
        return Task.objects.select_related(
            'assignee', 'created_by', 'project'
        ).get(
            id=task_id,
            tenant=tenant,
            is_active=True
        )
    except Task.DoesNotExist:
        return None