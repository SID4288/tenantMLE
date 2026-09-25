from django.core.exceptions import ValidationError
from django.db import models

# Create your models here.
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
        return f"{self.assignment.user.email} progress in {self.assignment.course.title}: {self.progress_percentage}%"
class Assignment(models.Model):
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="content_assignments",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    learning_material = models.TextField(blank=True, default="")
    task = models.TextField(blank=True, default="")
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Deterministic ordering within a course (id breaks order ties).
        ordering = ["course", "order", "id"]
        indexes = [
            models.Index(
                fields=["course", "order"],
                name="assignment_course_order_idx",
            ),
        ]

    def save(self, *args, **kwargs):
        # Model-level validation so every entry point (ORM, admin, future
        # APIs) enforces the same rules — never frontend-only.
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.course.title} #{self.order}: {self.title}"


class AssignmentProgress(models.Model):
    """Per-user progress on a single assignment (new learning structure)."""

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="progress_records",
    )
    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="assignment_progress",
    )
    completed = models.BooleanField(default=False)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["assignment", "user"],
                name="unique_assignment_progress",
            ),
        ]

    def clean(self):
        if self.assignment_id is None or self.user_id is None:
            # Field-level validation already reports missing relations.
            return
        course_tenant_id = self.assignment.course.tenant_id
        user_tenant_id = self.user.tenant_id
        if user_tenant_id is None or course_tenant_id != user_tenant_id:
            raise ValidationError(
                "Assignment progress is only possible for users belonging "
                "to the same tenant as the course."
            )

    def save(self, *args, **kwargs):
        # Model-level validation so every entry point (ORM, admin, future
        # APIs) enforces the same rules — never frontend-only.
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        state = "done" if self.completed else "open"
        return f"{self.user.email} [{state}] on {self.assignment.title}"