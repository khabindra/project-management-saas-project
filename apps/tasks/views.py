from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from django.db import transaction

from apps.tenants.permissions import IsValidTenant, IsTenantMember
from apps.tenants.models import Membership
from apps.accounts.models import User
from apps.projects.selectors import get_project_detail_for_tenant
from common.pagination import MemberCursorPagination

from .permissions import CanManageTask
from .selectors import (
    get_tasks_for_project,
    get_my_tasks_for_tenant,
    get_task_detail_for_tenant
)
from .services import create_task, update_task, delete_task
from .serializers import (
    TaskListSerializer,
    TaskDetailSerializer,
    CreateTaskSerializer,
    UpdateTaskSerializer,
)


class ProjectTaskListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/projects/{project_id}/tasks/ - List tasks for a project
    POST /api/projects/{project_id}/tasks/ - Create task in a project
    """
    permission_classes = [
        IsAuthenticated,
        IsValidTenant,
        IsTenantMember,
    ]
    pagination_class = MemberCursorPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateTaskSerializer
        return TaskListSerializer

    def _get_project(self):
        """Helper to get and cache project securely."""
        if not hasattr(self, '_project'):
            self._project = get_project_detail_for_tenant(
                tenant=self.request.tenant,
                project_id=self.kwargs.get('project_id')
            )
            if not self._project:
                raise NotFound('Project not found.')
        return self._project

    def get_queryset(self):
        project = self._get_project()
        return get_tasks_for_project(self.request.tenant, project)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        project = self._get_project()
        assignee_id = serializer.validated_data.get('assignee_id')
        assignee = None

        if assignee_id:
            # SECURITY: Prevent cross-tenant assignment
            is_member = Membership.objects.filter(
                tenant=request.tenant,
                user_id=assignee_id,
                is_active=True
            ).exists()
            
            if not is_member:
                raise ValidationError({"assignee_id": ["User is not a member of this tenant."]})
            
            # SECURITY: Only Admins/Owners can assign tasks
            if not request.membership.is_admin:
                raise ValidationError({"assignee_id": ["Only admins or owners can assign tasks."]})
            
            try:
                assignee = User.objects.get(id=assignee_id)
            except User.DoesNotExist:
                raise ValidationError({"assignee_id": ["User does not exist."]})

        # Pop assignee_id and pass the resolved User object to service
        task_data = {k: v for k, v in serializer.validated_data.items() if k != 'assignee_id'}
        
        task = create_task(
            tenant=request.tenant,
            project=project,
            user=request.user,
            assignee=assignee,
            **task_data
        )

        return Response({
            'message': 'Task created successfully.',
            'task': TaskListSerializer(task).data
        }, status=status.HTTP_201_CREATED)


class TenantMyTasksListView(generics.ListAPIView):
    """
    GET /api/tasks/my/ - List all tasks assigned to the logged-in user
    """
    permission_classes = [IsAuthenticated, IsValidTenant, IsTenantMember]
    pagination_class = MemberCursorPagination
    serializer_class = TaskListSerializer

    def get_queryset(self):
        return get_my_tasks_for_tenant(self.request.tenant, self.request.user)


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/tasks/{task_id}/ - Get task details
    PATCH  /api/tasks/{task_id}/ - Update task (OWNER/ADMIN only)
    DELETE /api/tasks/{task_id}/ - Soft delete task (OWNER/ADMIN only)
    """
    permission_classes = [
        IsAuthenticated,
        IsValidTenant,
        IsTenantMember,
        CanManageTask,
    ]
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return UpdateTaskSerializer
        return TaskDetailSerializer

    def get_object(self):
        task = get_task_detail_for_tenant(
            tenant=self.request.tenant,
            task_id=self.kwargs.get('task_id')
        )
        if not task:
            raise NotFound('Task not found.')
        return task

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        # REUSABILITY & PERFORMANCE: Handle assignee exactly like in CreateView
        assignee_id = serializer.validated_data.get('assignee_id')
        assignee = None

        if assignee_id:
            # SECURITY: Prevent cross-tenant assignment on update
            is_member = Membership.objects.filter(
                tenant=request.tenant,
                user_id=assignee_id,
                is_active=True
            ).exists()
            
            if not is_member:
                raise ValidationError({"assignee_id": ["Cannot assign task to non-tenant member."]})

            try:
                assignee = User.objects.get(id=assignee_id)
            except User.DoesNotExist:
                raise ValidationError({"assignee_id": ["User does not exist."]})

        # Pop assignee_id and pass the resolved User object to service
        task_data = {k: v for k, v in serializer.validated_data.items() if k != 'assignee_id'}
        
        update_task(task=instance, assignee=assignee, **task_data)

        return Response({
            'message': 'Task updated successfully.',
            'task': TaskDetailSerializer(instance).data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        delete_task(task=instance)
        return Response(
            {'message': 'Task deleted successfully.'},
            status=status.HTTP_200_OK
        )