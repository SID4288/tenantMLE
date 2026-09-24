from rest_framework.permissions import BasePermission
from accounts.models import UserRole


class IsAssignmentManager(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.role in [
            UserRole.SUPER_ADMIN,
            UserRole.ADMIN,
            UserRole.TENANT_ADMIN,
        ]


class IsProgressManager(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return request.user.role in [
            UserRole.SUPER_ADMIN,
            UserRole.ADMIN,
            UserRole.TENANT_ADMIN,
            UserRole.TENANT_USER,
        ]