from rest_framework.permissions import BasePermission
from accounts.models import UserRole

class IsCourseManager(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN, UserRole.TENANT_ADMIN]