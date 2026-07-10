from django.db.models import Count, Prefetch, Q, Subquery, OuterRef, IntegerField, Value
from django.db.models.functions import Coalesce
from rest_framework import generics, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from common.pagination import MemberCursorPagination

from .models import Tenant, Membership
from .serializers import (
    TenantListSerializer,
    TenantDetailSerializer,
    CreateTenantSerializer,
    UpdateTenantSerializer,
    InviteMemberSerializer,
    MembershipSerializer,
    UpdateRoleSerializer,
)
from .permissions import IsTenantMember, IsTenantOwner, IsTenantAdmin, IsValidTenant
from .services import (
    create_tenant, update_tenant, delete_tenant,
    invite_member, update_member_role, transfer_ownership,
    remove_member, leave_tenant
)

class MyTenantsListView(generics.ListAPIView):
    """
    List all tenants the logged-in user belongs to, including their role.
    Access: All authenticated users
    """
    permission_classes = [IsAuthenticated]
    serializer_class = TenantListSerializer
    pagination_class = MemberCursorPagination

    def get_queryset(self):
        user = self.request.user

        # Subquery 1: Get user's role in each tenant
        user_role_subquery = Membership.objects.filter(
            user=user,
            tenant=OuterRef('pk'),
            is_active=True
        ).values('role')[:1]

        # Subquery 2: Get total active member count for each tenant
        # This runs INDEPENDENTLY of the main filter
        member_count_subquery = Membership.objects.filter(
            tenant=OuterRef('pk'),
            is_active=True
        ).values('tenant').annotate(
            count=Count('pk', output_field=IntegerField())
        ).values('count')

        return (
            Tenant.objects
            .filter(
                memberships__user=user,
                memberships__is_active=True,
                is_active=True
            )
            .annotate(
                # Coalesce handles NULL if subquery returns nothing
                active_member_count=Coalesce(
                    Subquery(member_count_subquery),
                    Value(0, output_field=IntegerField()),
                    output_field=IntegerField()
                ),
                user_role=Subquery(user_role_subquery)
            )
            .select_related('owner')
            .distinct()
        )
    

class TenantCreateView(generics.CreateAPIView):
    """
    Create a new tenant. Creator becomes OWNER.
    Access: All authenticated users
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CreateTenantSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        tenant = create_tenant(
            name=serializer.validated_data['name'],
            owner=self.request.user
        )
        tenant.active_member_count = 1

        return Response(
            TenantListSerializer(tenant).data,
            status=status.HTTP_201_CREATED
        )


class TenantDetailView(generics.RetrieveAPIView):
    """
    Get tenant details including all active members.
    Access: OWNER, ADMIN, MEMBER
    """
    permission_classes = [IsAuthenticated, IsValidTenant, IsTenantMember]
    serializer_class = TenantDetailSerializer

    def get_object(self):
        active_memberships = Membership.objects.filter(
            is_active=True
        ).select_related('user').order_by('created_at')

        return (
            Tenant.objects
            .prefetch_related(Prefetch('memberships', queryset=active_memberships))
            .select_related('owner')
            .get(pk=self.request.tenant.pk)
        )


class TenantUpdateView(generics.UpdateAPIView):
    """
    Update tenant name/slug.
    Access: OWNER only
    """
    permission_classes = [IsAuthenticated, IsValidTenant, IsTenantOwner]
    serializer_class = UpdateTenantSerializer
    http_method_names = ['patch']

    def get_object(self):
        return self.request.tenant

    def perform_update(self, serializer):
        update_tenant(
            tenant=self.request.tenant,
            name=serializer.validated_data['name']
        )


class TenantDeleteView(views.APIView):
    """
    Soft-delete the tenant.
    Access: OWNER only
    """
    permission_classes = [IsAuthenticated, IsValidTenant, IsTenantOwner]

    def post(self, request):
        delete_tenant(tenant=request.tenant)
        return Response({'message': 'Tenant deleted successfully.'})


class TenantMembersListView(generics.ListAPIView):
    """
    List all active members of the tenant.
    Access: OWNER, ADMIN, MEMBER
    """
    permission_classes = [IsAuthenticated, IsValidTenant, IsTenantMember]
    serializer_class = MembershipSerializer
    pagination_class = MemberCursorPagination

    def get_queryset(self):
        return (
            Membership.objects
            .filter(tenant=self.request.tenant, is_active=True)
            .select_related('user')
            .order_by('created_at')
        )


class InviteMemberView(views.APIView):
    """
    Invite a user to the tenant.
    Access: 
      - OWNER can invite as ADMIN or MEMBER
      - ADMIN can invite as MEMBER only
    """
    permission_classes = [IsAuthenticated, IsValidTenant, IsTenantAdmin]

    def post(self, request):
        serializer = InviteMemberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        role = serializer.validated_data['role']

        # Only OWNER can invite as ADMIN
        if role == Membership.Role.ADMIN and not request.membership.is_owner:
            return Response(
                {'error': 'Only the tenant owner can invite users as ADMIN.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            membership = invite_member(
                tenant=request.tenant,
                email=serializer.validated_data['email'],
                role=role
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': 'Member invited successfully.',
            'membership': MembershipSerializer(membership).data
        }, status=status.HTTP_201_CREATED)


class UpdateMemberRoleView(views.APIView):
    """
    Change a member's role (ADMIN ↔ MEMBER only).
    For ownership transfer, use /transfer-ownership/ endpoint.
    Access: OWNER only
    """
    permission_classes = [IsAuthenticated, IsValidTenant, IsTenantOwner]

    def patch(self, request, membership_id):
        try:
            membership = Membership.objects.get(
                id=membership_id,
                tenant=request.tenant,
                is_active=True
            )
        except Membership.DoesNotExist:
            return Response(
                {'error': 'Membership not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Cannot change OWNER's role via this endpoint
        if membership.is_owner:
            return Response(
                {'error': 'Cannot change owner role. Use /transfer-ownership/ endpoint.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = UpdateRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        updated = update_member_role(
            membership=membership,
            role=serializer.validated_data['role']
        )

        return Response({
            'message': 'Member role updated.',
            'membership': MembershipSerializer(updated).data,
        })


class TransferOwnershipView(views.APIView):
    """
    Transfer ownership to another member.
    
    This is atomic:
    - Target member becomes OWNER
    - Current owner becomes ADMIN
    - Tenant.owner field is updated
    
    After transfer, the former owner can leave the tenant.
    Access: OWNER only
    """
    permission_classes = [IsAuthenticated, IsValidTenant, IsTenantOwner]

    def post(self, request, membership_id):
        try:
            target_membership = Membership.objects.select_for_update().get(
                id=membership_id,
                tenant=request.tenant,
                is_active=True
            )
        except Membership.DoesNotExist:
            return Response(
                {'error': 'Membership not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            # Re-fetch current owner membership with lock
            current_owner_membership = (
                Membership.objects
                .select_for_update()
                .get(
                    user=request.user,
                    tenant=request.tenant,
                    is_active=True,
                    role=Membership.Role.OWNER
                )
            )
        except Membership.DoesNotExist:
            return Response(
                {'error': 'You are not the owner.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            updated = transfer_ownership(
                tenant=request.tenant,
                current_owner_membership=current_owner_membership,
                target_membership=target_membership
            )
        except ValueError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': 'Ownership transferred successfully.',
            'membership': MembershipSerializer(updated).data
        })


class RemoveMemberView(views.APIView):
    """
    Remove a member from the tenant.
    Access:
      - OWNER can remove ADMINs and MEMBERs
      - ADMIN can remove MEMBERs only (not other ADMINs)
    """
    permission_classes = [IsAuthenticated, IsValidTenant, IsTenantAdmin]

    def post(self, request, membership_id):
        try:
            membership = Membership.objects.get(
                id=membership_id,
                tenant=request.tenant,
                is_active=True
            )
        except Membership.DoesNotExist:
            return Response(
                {'error': 'Membership not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Cannot remove the owner
        if membership.is_owner:
            return Response(
                {'error': 'Use the /leave/ endpoint to leave the tenant.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Only OWNER can remove ADMINs
        if membership.role == Membership.Role.ADMIN and not request.membership.is_owner:
            return Response(
                {'error': 'Only the tenant owner can remove admins.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Cannot remove yourself - use leave endpoint
        if membership.user == request.user:
            return Response(
                {'error': 'Use the /leave/ endpoint to leave the tenant.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        remove_member(membership=membership)
        return Response({'message': 'Member removed successfully.'})


class LeaveTenantView(views.APIView):
    """
    Leave the tenant.
    Access: OWNER (blocked), ADMIN, MEMBER
    Note: Owner must transfer ownership before leaving.
    """
    permission_classes = [IsAuthenticated, IsValidTenant, IsTenantMember]

    def post(self, request):
        # select_for_update() prevents TOCTOU race on owner check
        # DoesNotExist won't occur because IsTenantMember already verified membership
        membership = (
            Membership.objects
            .select_for_update()
            .get(
                user=request.user,
                tenant=request.tenant,
                is_active=True
            )
        )
        try:
            leave_tenant(membership=membership)
            return Response({'message': 'You have left the tenant.'})
        except ValueError as exc:
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )