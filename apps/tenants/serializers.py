from rest_framework import serializers
from .models import Tenant, Membership
from apps.accounts.serializers import UserSerializer


class MembershipSerializer(serializers.ModelSerializer):
    """Serializer to return user details within a membership."""
    user = UserSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ['id', 'user', 'role', 'is_active', 'created_at']
        read_only_fields = fields
class TenantListSerializer(serializers.ModelSerializer):
    member_count = serializers.SerializerMethodField()
    user_role = serializers.CharField(read_only=True)

    class Meta:
        model = Tenant
        fields = ['id', 'name', 'slug', 'user_role', 'member_count', 'created_at']
        read_only_fields = fields

    def get_member_count(self, obj):
        # Use the annotated value from the queryset
        if hasattr(obj, 'active_member_count'):
            return obj.active_member_count
        # Fallback (shouldn't happen with proper queryset)
        return obj.memberships.filter(is_active=True).count()


class TenantDetailSerializer(serializers.ModelSerializer):
    memberships = MembershipSerializer(many=True, read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug', 'owner', 'is_active',
            'member_count', 'memberships', 'created_at', 'updated_at'
        ]
        read_only_fields = fields

    def get_member_count(self, obj):
        if hasattr(obj, 'active_member_count'):
            return obj.active_member_count
        return obj.memberships.filter(is_active=True).count()


class CreateTenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['name']

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError('Name cannot be empty.')
        return value


class UpdateTenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ['name']

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError('Name cannot be empty.')
        return value


# OWNER excluded — ownership transfer uses dedicated endpoint
_INVITE_ROLE_CHOICES = [
    (Membership.Role.ADMIN, Membership.Role.ADMIN.label),
    (Membership.Role.MEMBER, Membership.Role.MEMBER.label),
]


class InviteMemberSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=_INVITE_ROLE_CHOICES)


# OWNER excluded — use /transfer-ownership/ endpoint instead
_UPDATE_ROLE_CHOICES = [
    (Membership.Role.ADMIN, Membership.Role.ADMIN.label),
    (Membership.Role.MEMBER, Membership.Role.MEMBER.label),
]


class UpdateRoleSerializer(serializers.Serializer):
    """
    Used by UpdateMemberRoleView.
    OWNER role excluded — ownership transfer is a separate endpoint.
    """
    role = serializers.ChoiceField(choices=_UPDATE_ROLE_CHOICES)

