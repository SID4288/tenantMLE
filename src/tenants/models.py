from django.db import models

# Create your models here.
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

    def __str__(self):
        return self.name