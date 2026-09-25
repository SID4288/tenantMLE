from django.contrib import admin

from .models import CourseAssignment, LearningProgress


@admin.register(CourseAssignment)
class CourseAssignmentAdmin(admin.ModelAdmin):
    list_display = ("id", "course", "user", "assigned_at")
    list_filter = ("course",)
    search_fields = ("course__title", "user__email")


@admin.register(LearningProgress)
class LearningProgressAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "assignment",
        "progress_percentage",
        "started_at",
        "completed_at",
        "updated_at",
    )
    list_filter = ("progress_percentage",)