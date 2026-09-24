from rest_framework import serializers

from accounts.models import UserRole
from .models import CourseAssignment, LearningProgress


class CourseAssignmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourseAssignment
        fields = ["id", "course", "user", "assigned_at"]
        read_only_fields = ["id", "assigned_at"]

    def validate(self, attrs):
        course = attrs["course"]
        user = attrs["user"]

        # The course and user must belong to the same tenant
        if course.tenant_id != user.tenant_id:
            raise serializers.ValidationError(
                "Course and user must belong to the same tenant."
            )

        # Only tenant users should receive course assignments
        if user.role != UserRole.TENANT_USER:
            raise serializers.ValidationError(
                "Courses can only be assigned to tenant users."
            )

        request = self.context["request"]
        requester = request.user

        # Tenant Admin can only assign within their own tenant
        if requester.role == UserRole.TENANT_ADMIN:
            if course.tenant_id != requester.tenant_id:
                raise serializers.ValidationError(
                    "You cannot assign courses outside your tenant."
                )

        return attrs

class LearningProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningProgress
        fields = [
            "id",
            "assignment",
            "progress_percentage",
            "started_at",
            "completed_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "assignment",
            "updated_at",
        ]

    def validate_progress_percentage(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError(
                "Progress must be between 0 and 100."
            )

        return value