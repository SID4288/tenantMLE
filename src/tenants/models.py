from django.db import models
from django.utils import timezone


class TenantStatus(models.TextChoices):
    TRIAL_ACTIVE = "TRIAL_ACTIVE", "Trial Active"
    EXPIRED = "EXPIRED", "Expired"
    ACTIVE = "ACTIVE", "Active"


class Tenant(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    status = models.CharField(
        max_length=20,
        choices=TenantStatus.choices,
        default=TenantStatus.TRIAL_ACTIVE,
    )
    trial_started_at = models.DateTimeField()
    trial_ends_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def refresh_status(self):
        if (
            self.status == TenantStatus.TRIAL_ACTIVE
            and timezone.now() >= self.trial_ends_at
        ):
            self.status = TenantStatus.EXPIRED
            self.save(update_fields=["status", "updated_at"])

        return self.status

    def reactivate(self):
        self.status = TenantStatus.ACTIVE
        self.save(update_fields=["status", "updated_at"])
        return self.status

    def __str__(self):
        return self.name