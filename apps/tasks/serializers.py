from rest_framework import serializers
from .models import Task


# REUSABILITY: Mixin to prevent duplicating validation logic
class TaskValidationMixin:
    """Reusable validation for task fields."""
    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Task title cannot be empty.")
        if len(value) > 255:
            raise serializers.ValidationError("Task title cannot exceed 255 characters.")
        return value

    def validate_description(self, value):
        if len(value) > 10000:
            raise serializers.ValidationError("Description cannot exceed 10000 characters.")
        return value


class TaskListSerializer(serializers.ModelSerializer):
    assignee_email = serializers.EmailField(source='assignee.email', read_only=True, default=None)
    assignee_name = serializers.CharField(source='assignee.full_name', read_only=True, default=None)
    project_name = serializers.CharField(source='project.name', read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'title', 'status', 'project_name',
            'assignee_email', 'assignee_name', 'created_at'
        ]


class TaskDetailSerializer(TaskListSerializer):
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)

    class Meta(TaskListSerializer.Meta):
        fields = TaskListSerializer.Meta.fields + [
            'description', 'created_by_email', 'created_by_name', 'updated_at'
        ]


class CreateTaskSerializer(TaskValidationMixin, serializers.ModelSerializer):
    assignee_id = serializers.UUIDField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = Task
        fields = ['title', 'description', 'assignee_id']


class UpdateTaskSerializer(TaskValidationMixin, serializers.ModelSerializer):
    assignee_id = serializers.UUIDField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'assignee_id']