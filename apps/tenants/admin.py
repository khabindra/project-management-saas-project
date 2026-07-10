from django.contrib import admin
from .models import Tenant, Membership


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['id','name', 'slug', 'owner', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'slug', 'owner__email']


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['id','user', 'tenant', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active']
    search_fields = ['user__email', 'tenant__name']