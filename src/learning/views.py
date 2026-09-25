from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from accounts.models import UserRole
from .models import CourseAssignment, LearningProgress
from .permissions import IsAssignmentManager, IsProgressManager
from .serializers import (
    CourseAssignmentSerializer,
    LearningProgressSerializer,
)
from django.utils import timezone
from accounts.permissions import IsTenantActive

class CourseAssignmentViewSet(ModelViewSet):
    serializer_class = CourseAssignmentSerializer

    def get_permissions(self):
        permission_classes = [
            IsAuthenticated,
            IsTenantActive,
        ]

        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes.append(IsAssignmentManager)

        return [permission() for permission in permission_classes]
    def get_queryset(self):
        user = self.request.user

        # Platform-level users can see assignments across tenants
        if user.role in [
            UserRole.SUPER_ADMIN,
            UserRole.ADMIN,
            UserRole.SUPER_VIEWER,
        ]:
            return CourseAssignment.objects.all()

        # Tenant Admin can only see assignments
        # belonging to their tenant
        if user.role == UserRole.TENANT_ADMIN:
            return CourseAssignment.objects.filter(
                course__tenant_id=user.tenant_id
            )

        # Tenant User can only see their own assignments
        if user.role == UserRole.TENANT_USER:
            return CourseAssignment.objects.filter(
                user_id=user.id
            )

        return CourseAssignment.objects.none()

    def perform_create(self, serializer):
        assignment = serializer.save()
        LearningProgress.objects.create(
            assignment=assignment,
        )

class LearningProgressViewSet(ModelViewSet):
    serializer_class = LearningProgressSerializer

    def get_permissions(self):
        permission_classes = [
            IsAuthenticated,
            IsTenantActive,
        ]

        if self.action in ["create", "update", "partial_update", "destroy"]:
            permission_classes.append(IsProgressManager)

        return [permission() for permission in permission_classes]

    def get_queryset(self):
        user = self.request.user

        if user.role in [
            UserRole.SUPER_ADMIN,
            UserRole.ADMIN,
            UserRole.SUPER_VIEWER,
        ]:
            return LearningProgress.objects.all()

        if user.role == UserRole.TENANT_ADMIN:
            return LearningProgress.objects.filter(
                assignment__course__tenant_id=user.tenant_id
            )

        if user.role == UserRole.TENANT_USER:
            return LearningProgress.objects.filter(
                assignment__user_id=user.id
            )

        return LearningProgress.objects.none()
    
    def create(self, request, *args, **kwargs):
        return Response(
        {"detail": "Progress is created automatically with a course assignment."},
        status=status.HTTP_405_METHOD_NOT_ALLOWED,
    )
    def perform_update(self, serializer):
        progress = serializer.save()

        if progress.progress_percentage > 0 and progress.started_at is None:
            progress.started_at = timezone.now()

        if progress.progress_percentage == 100 and progress.completed_at is None:
            progress.completed_at = timezone.now()

        progress.save()