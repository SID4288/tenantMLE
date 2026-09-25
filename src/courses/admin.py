from django.contrib import admin

from .models import Course


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "tenant",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "title",
        "description",
    )
    list_filter = (
        "tenant",
    )
