from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class UserRole(models.TextChoices):
    SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
    ADMIN = "ADMIN", "Admin"
    SUPER_VIEWER = "SUPER_VIEWER", "Super Viewer"
    TENANT_ADMIN = "TENANT_ADMIN", "Tenant Admin"
    TENANT_USER = "TENANT_USER", "Tenant User"

class User(AbstractUser):
    email = models.EmailField(unique=True)
    role = models.CharField(
        max_length=20,
        choices=UserRole.choices,
        default=UserRole.TENANT_USER,
    )
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.PROTECT, null=True, blank=True, related_name='users')
    # Forced password rotation (e.g. first login with a one-time temp password).
    must_change_password = models.BooleanField(default=False)
    # Ensures the one-time temp password is revealed exactly once.
    temp_password_revealed = models.BooleanField(default=False)


    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.email