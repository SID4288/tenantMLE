from django.core.exceptions import ValidationError
from django.db import models


class CourseAssignment(models.Model):
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="course_assignments",
    )
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["course", "user"],
                name="unique_course_assignment",
            ),
        ]

    def __str__(self):
        return f"{self.user.email} → {self.course.title}"


class LearningProgress(models.Model):
    assignment = models.OneToOneField(
        "CourseAssignment",
        on_delete=models.CASCADE,
        related_name="progress",
    )
    progress_percentage = models.PositiveIntegerField(default=0)

    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"{self.assignment.user.email} progress in "
            f"{self.assignment.course.title}: "
            f"{self.progress_percentage}%"
        )
