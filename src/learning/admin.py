from django.contrib import admin

from .models import (
    Assignment,
    AssignmentProgress,
    CourseAssignment,
    LearningProgress,
)


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "course",
        "order",
        "created_at",
        "updated_at",
    )
    search_fields = (
        "title",
        "description",
        "task",
        "course__title",
    )
    list_filter = (
        "course",
    )


@admin.register(AssignmentProgress)
class AssignmentProgressAdmin(admin.ModelAdmin):
    pass


@admin.register(CourseAssignment)
class CourseAssignmentAdmin(admin.ModelAdmin):
    pass


@admin.register(LearningProgress)
class LearningProgressAdmin(admin.ModelAdmin):
    pass
