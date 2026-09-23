from django.contrib import admin

# Register your models here.
from .models import Tenant

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'status', 'trial_started_at', 'trial_ends_at', 'created_at', 'updated_at')
    search_fields = ('name', 'slug')
    list_filter = ('status',)