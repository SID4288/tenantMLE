from rest_framework import serializers

from accounts.models import UserRole
from .models import Course

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = [
            "id",
            "tenant",
            "title",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]
        extra_kwargs = {
            "tenant": {"required": False},
        }

    def validate(self, attrs):
        request = self.context.get("request")
        is_tenant_admin = (
            request
            and request.user.role == UserRole.TENANT_ADMIN
        )
        if (
            self.instance is None
            and attrs.get("tenant") is None
            and not is_tenant_admin
        ):
            raise serializers.ValidationError(
                {"tenant": "A tenant is required when creating a course."}
            )

        return attrs

    def perform_create(self, serializer):
        user = self.request.user

        if user.role == UserRole.TENANT_ADMIN:
            serializer.save(tenant=user.tenant)
        else:
            serializer.save()