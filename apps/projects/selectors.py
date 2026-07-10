from .models import Project


def get_projects_for_tenant(tenant):
    """
    Get all active projects for a specific tenant.
    """
    return Project.objects.filter(
        tenant=tenant,
        is_active=True
    ).select_related('created_by')


def get_project_detail_for_tenant(tenant, project_id) -> Project | None:
    """
    Get a single project, ensuring it belongs to the tenant.
    """
    try:
        return Project.objects.select_related('created_by').get(
            id=project_id,
            tenant=tenant,
            is_active=True
        )
    except Project.DoesNotExist:
        return None