from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
# Register your models here.
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ( "email","username","role","tenant","is_active",)
    list_filter = ( "role","is_active", "tenant")
    search_fields = ( "email", "username")
