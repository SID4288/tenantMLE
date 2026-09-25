from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

from .models import Tenant, TenantStatus


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = [
            "id",
            "name",
            "slug",
            "status",
            "trial_started_at",
            "trial_ends_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "trial_started_at",
            "trial_ends_at",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        trial_started_at = timezone.now()
        return Tenant.objects.create(
            **validated_data,
            status=TenantStatus.TRIAL_ACTIVE,
            trial_started_at=trial_started_at,
            trial_ends_at=trial_started_at + timedelta(days=30),
        )
