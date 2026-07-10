from django.urls import path
from .views import (
    ProjectTaskListCreateView,
    TenantMyTasksListView,
    TaskDetailView,
)

urlpatterns = [
    # 1. Hybrid: Nested under Projects
    path(
        'projects/<uuid:project_id>/tasks/',
        ProjectTaskListCreateView.as_view(),
        name='project-tasks'
    ),

    # 2. Hybrid: Tenant-wide dashboard view
    path(
        'tasks/my/',
        TenantMyTasksListView.as_view(),
        name='my-tasks'
    ),

    # 3. Hybrid: Flat resource for Detail/Update/Delete
    path(
        'tasks/<uuid:task_id>/',
        TaskDetailView.as_view(),
        name='task-detail'
    ),
]