from rest_framework.permissions import BasePermission
from tenants.models import TenantStatus
from .models import UserRole


class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == UserRole.SUPER_ADMIN

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == UserRole.ADMIN

class IsSuperViewer(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == UserRole.SUPER_VIEWER

class IsTenantAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == UserRole.TENANT_ADMIN

class IsTenantUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == UserRole.TENANT_USER

class IsUserManager(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.role == UserRole.SUPER_VIEWER:
            return request.method in ["GET", "HEAD", "OPTIONS"]

        return request.user.role in [
            UserRole.SUPER_ADMIN,
            UserRole.ADMIN,
            UserRole.TENANT_ADMIN,
        ]
class IsTenantActive(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        user = request.user

        # Platform-level users are not restricted by tenant expiration.
        if user.role in [
            UserRole.SUPER_ADMIN,
            UserRole.ADMIN,
            UserRole.SUPER_VIEWER,
        ]:
            return True

        # Tenant users must belong to a tenant.
        if not user.tenant:
            return False

        # Refresh the tenant lifecycle state before checking access.
        user.tenant.refresh_status()

        return user.tenant.status != TenantStatus.EXPIRED