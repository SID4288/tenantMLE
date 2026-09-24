from rest_framework.permissions import BasePermission

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

        if request.user.role in [
            UserRole.SUPER_ADMIN,
            UserRole.ADMIN,
            UserRole.TENANT_ADMIN,
        ]:
            return True

        return False