from django.shortcuts import render

# Create your views here.
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from .models import Course
from .serializers import CourseSerializer
from accounts.models import UserRole
from .permissions import IsCourseManager
class CourseViewSet(ModelViewSet):
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role in [UserRole.SUPER_ADMIN, UserRole.ADMIN]:
            return Course.objects.all()

        if user.role in [UserRole.TENANT_ADMIN, UserRole.TENANT_USER]:
            return Course.objects.filter(tenant_id=user.tenant_id)

        return Course.objects.none()

    def get_permissions(self):

        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            self.permission_classes = [IsAuthenticated, IsCourseManager]
        else:
            self.permission_classes = [IsAuthenticated]

        return [permission() for permission in self.permission_classes]

    def perform_create(self, serializer):
        user = self.request.user

        if user.role == UserRole.TENANT_ADMIN:
            serializer.save(tenant=user.tenant)
        else:
            serializer.save()