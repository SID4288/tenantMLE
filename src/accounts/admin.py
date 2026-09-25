from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        (
            "Platform / Tenant",
            {
                "fields": (
                    "role",
                    "tenant",
                )
            },
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "Platform / Tenant",
            {
                "fields": (
                    "email",
                    "role",
                    "tenant",
                )
            },
        ),
    )

    list_display = (
        "username",
        "email",
        "role",
        "tenant",
        "is_active",
        "is_staff",
    )

    list_filter = (
        "role",
        "tenant",
        "is_active",
        "is_staff",
    )