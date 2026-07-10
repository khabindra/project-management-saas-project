from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from apps.tenants.permissions import IsValidTenant, IsTenantMember
from common.pagination import MemberCursorPagination

from .permissions import IsProjectAdminOrReadOnly
from .selectors import get_projects_for_tenant, get_project_detail_for_tenant
from .services import create_project, update_project, delete_project
from .serializers import (
    ProjectListSerializer,
    ProjectDetailSerializer,
    CreateProjectSerializer,
    UpdateProjectSerializer,
)


class ProjectListCreateView(generics.ListCreateAPIView):
    """
    GET    /api/projects/  - List projects (all members)
    POST   /api/projects/  - Create project (OWNER/ADMIN only)
    """
    permission_classes = [
        IsAuthenticated,
        IsValidTenant,
        IsTenantMember,
        IsProjectAdminOrReadOnly,
    ]
    pagination_class = MemberCursorPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateProjectSerializer
        return ProjectListSerializer

    def get_queryset(self):
        return get_projects_for_tenant(self.request.tenant)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            project = create_project(
                tenant=request.tenant,
                user=request.user,
                **serializer.validated_data
            )
        except ValueError as e:
            raise ValidationError(detail=str(e))

        return Response({
            'message': 'Project created successfully.',
            'project': ProjectListSerializer(project).data
        }, status=status.HTTP_201_CREATED)


class ProjectDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET     /api/projects/{id}/  - Get project (all members)
    PATCH   /api/projects/{id}/  - Update project (OWNER/ADMIN only)
    DELETE  /api/projects/{id}/  - Soft delete project (OWNER/ADMIN only)
    """
    permission_classes = [
        IsAuthenticated,
        IsValidTenant,
        IsTenantMember,
        IsProjectAdminOrReadOnly,
    ]
    http_method_names = ['get', 'patch', 'delete', 'head', 'options']

    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return UpdateProjectSerializer
        return ProjectDetailSerializer

    def get_object(self):
        project = get_project_detail_for_tenant(
            tenant=self.request.tenant,
            project_id=self.kwargs.get('project_id')
        )
        if not project:
            raise NotFound('Project not found.')
        return project

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)

        try:
            update_project(project=instance, **serializer.validated_data)
        except ValueError as e:
            raise ValidationError(detail=str(e))

        return Response({
            'message': 'Project updated successfully.',
            'project': ProjectDetailSerializer(instance).data
        })

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        delete_project(project=instance)
        return Response(
            {'message': 'Project deleted successfully.'},
            status=status.HTTP_200_OK  # FIX: 200 for soft delete with message body
        )