from django.urls import path
from .views import (
    MyTenantsListView,
    TenantCreateView,
    TenantDetailView,
    TenantUpdateView,
    TenantDeleteView,
    TenantMembersListView,
    InviteMemberView,
    UpdateMemberRoleView,
    TransferOwnershipView,
    RemoveMemberView,
    LeaveTenantView,
)

urlpatterns = [
    # My tenants (no X-Tenant-ID needed)
    path('my/', MyTenantsListView.as_view(), name='my-tenants'),
    path('create/', TenantCreateView.as_view(), name='create-tenant'),

    # Tenant-specific (X-Tenant-ID required in header)
    path('', TenantDetailView.as_view(), name='tenant-detail'),
    path('update/', TenantUpdateView.as_view(), name='tenant-update'),
    path('delete/', TenantDeleteView.as_view(), name='tenant-delete'),

    # Members
    path('members/', TenantMembersListView.as_view(), name='tenant-members'),
    path('members/invite/', InviteMemberView.as_view(), name='invite-member'),
    path(
        'members/<uuid:membership_id>/role/',
        UpdateMemberRoleView.as_view(),
        name='update-member-role'
    ),
    path(
        'members/<uuid:membership_id>/transfer-ownership/',
        TransferOwnershipView.as_view(),
        name='transfer-ownership'
    ),
    path(
        'members/<uuid:membership_id>/remove/',
        RemoveMemberView.as_view(),
        name='remove-member'
    ),
    path('leave/', LeaveTenantView.as_view(), name='leave-tenant'),
]