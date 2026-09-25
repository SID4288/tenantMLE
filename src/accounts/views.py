from django.shortcuts import render
# Create your views here.
from rest_framework.decorators import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.permissions import IsSuperAdmin, IsTenantActive
from rest_framework.viewsets import ModelViewSet
from .permissions import IsUserManager
from .models import User, UserRole
from .serializers import UserSerializer

class MeView(APIView):
    permission_classes = [IsAuthenticated]  # Allow any user (authenticated or not) to access this view
    def get(self, request):
        user = request.user

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "tenant": user.tenant_id,
        })
class SuperAdminTestView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        return Response({
            "message": "You are allowed to access this endpoint.",
            "role": request.user.role,
        })

class UserViewSet(ModelViewSet):
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role in [
            UserRole.SUPER_ADMIN,
            UserRole.ADMIN,
            UserRole.SUPER_VIEWER,
        ]:
            return User.objects.all()

        if user.role == UserRole.TENANT_ADMIN:
            return User.objects.filter(
                tenant_id=user.tenant_id
            )

        return User.objects.none()

    def perform_create(self, serializer):
        user = self.request.user

        if user.role == UserRole.TENANT_ADMIN:
            serializer.save(
                tenant=user.tenant
            )
        else:
            serializer.save()

    def get_permissions(self):
        return [
            IsAuthenticated(),
            IsTenantActive(),
            IsUserManager(),
        ]