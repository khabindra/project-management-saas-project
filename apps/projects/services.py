import re
from django.db import transaction, IntegrityError
from .models import Project


def _normalize_project_name(name: str) -> str:
    """
    Normalize project name for case-insensitive, space-insensitive comparison.
    
    Examples:
        "My Project"  → "my project"
        "MY  PROJECT" → "my project"
        "MyProject"   → "myproject"
    """
    # Strip leading/trailing whitespace, collapse internal whitespace, lowercase
    return re.sub(r'\s+', ' ', name.strip()).lower()


@transaction.atomic
def create_project(*, tenant, user, name: str, description: str = "") -> Project:
    name_lower = _normalize_project_name(name)
    
    try:
        project = Project.objects.create(
            tenant=tenant,
            created_by=user,
            name=name,           # Store original for display
            name_lower=name_lower,  # Store normalized for uniqueness
            description=description
        )
    except IntegrityError:
        raise ValueError(
            f'A project named "{name}" already exists in this tenant.'
        )
    return project


@transaction.atomic
def update_project(*, project, **kwargs) -> Project:
    update_fields = ['updated_at']

    if 'name' in kwargs:
        project.name = kwargs['name']
        project.name_lower = _normalize_project_name(kwargs['name'])
        update_fields.extend(['name', 'name_lower'])

    if 'description' in kwargs:
        project.description = kwargs['description']
        update_fields.append('description')

    if len(update_fields) == 1:
        raise ValueError('No valid fields provided for update.')

    try:
        project.save(update_fields=update_fields)
    except IntegrityError:
        raise ValueError(
            f'A project named "{kwargs.get("name", "")}" already exists in this tenant.'
        )
    return project


@transaction.atomic
def delete_project(*, project) -> None:
    project.is_active = False
    project.save(update_fields=['is_active', 'updated_at'])