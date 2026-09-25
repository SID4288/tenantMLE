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
            "tenant",
            "created_at",
            "updated_at",
        ]

    def perform_create(self, serializer):
        user = self.request.user

        if user.role == UserRole.TENANT_ADMIN:
            serializer.save(tenant=user.tenant)
        else:
            serializer.save()