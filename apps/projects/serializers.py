from rest_framework import serializers
from .models import Project


class ProjectListSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(
        source='created_by.email',
        read_only=True
    )
    created_by_name = serializers.CharField(
        source='created_by.full_name',
        read_only=True
    )

    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description',
            'created_by_email', 'created_by_name',
            'created_at'
        ]


class ProjectDetailSerializer(ProjectListSerializer):
    class Meta(ProjectListSerializer.Meta):
        fields = ProjectListSerializer.Meta.fields + ['updated_at']


class CreateProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['name', 'description']

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Project name cannot be empty.")
        if len(value) > 255:
            raise serializers.ValidationError("Project name cannot exceed 255 characters.")
        return value

    def validate_description(self, value):
        if len(value) > 5000:
            raise serializers.ValidationError(
                "Description cannot exceed 5000 characters."
            )
        return value


class UpdateProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['name', 'description']
        extra_kwargs = {
            'name': {'required': False},
            'description': {'required': False},
        }

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Project name cannot be empty.")
        if len(value) > 255:
            raise serializers.ValidationError("Project name cannot exceed 255 characters.")
        return value

    def validate_description(self, value):
        if len(value) > 5000:
            raise serializers.ValidationError(
                "Description cannot exceed 5000 characters."
            )
        return value