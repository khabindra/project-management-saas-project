from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['id','title', 'project', 'tenant', 'status', 'assignee', 'is_active', 'created_at']
    list_filter = ['status', 'is_active', 'created_at']
    search_fields = ['title', 'project__name']
    raw_id_fields = ['tenant', 'project', 'assignee', 'created_by']
    
    # Reliability: Ensure soft-deleted tasks don't clutter the default admin view
    # def get_queryset(self, request):
    #     return super().get_queryset(request).filter(is_active=True)