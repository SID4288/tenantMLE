from django.shortcuts import render
# Create your views here.
from rest_framework import status
from rest_framework.decorators import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from accounts.permissions import IsSuperAdmin, IsTenantActive
from rest_framework.viewsets import ModelViewSet
from django.db import transaction
from .permissions import IsUserManager
from .models import User, UserRole
from .serializers import (
    ChangePasswordSerializer,
    TenantApplicationSerializer,
    TenantUserRegistrationSerializer,
    UserSerializer,
)
from tenants.models import TenantStatus

import secrets
import string

TEMP_PASSWORD_LENGTH = 12


def _mint_temp_password():
    alphabet = string.ascii_letters + string.digits
    return "".join(
        secrets.choice(alphabet) for _ in range(TEMP_PASSWORD_LENGTH)
    )

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
            "must_change_password": user.must_change_password,
        })
class SuperAdminTestView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        return Response({
            "message": "You are allowed to access this endpoint.",
            "role": request.user.role,
        })


class TenantUserRegistrationView(APIView):
    """Anonymous registration as TENANT_USER in an existing tenant."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TenantUserRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "tenant": user.tenant_id,
            },
            status=status.HTTP_201_CREATED,
        )


class TenantApplicationView(APIView):
    """Anonymous application to create a new organization (PENDING)."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TenantApplicationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        tenant = user.tenant
        return Response(
            {
                "detail": (
                    "Application received. Your organization is pending "
                    "approval; you will be able to log in once approved."
                ),
                "tenant": {
                    "id": tenant.id,
                    "name": tenant.name,
                    "slug": tenant.slug,
                    "status": tenant.status,
                },
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role,
                    "tenant": user.tenant_id,
                    "is_active": user.is_active,
                },
            },
            status=status.HTTP_201_CREATED,
        )


class ApplicationStatusView(APIView):
    """Anonymous application-status check for organization applicants.

    Looks the application up by admin email. On the first check after
    approval, mints the one-time temporary password and reveals it exactly
    once; later checks never return it again.
    """

    permission_classes = [AllowAny]

    @transaction.atomic
    def post(self, request):
        email = (request.data.get("admin_email") or "").strip()
        if not email:
            return Response(
                {"detail": "admin_email is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            user = (
                User.objects.select_for_update()
                .select_related("tenant")
                .get(
                    email__iexact=email,
                    role=UserRole.TENANT_ADMIN,
                    tenant__isnull=False,
                )
            )
        except User.DoesNotExist:
            return Response(
                {"detail": "No application found for this email."},
                status=status.HTTP_404_NOT_FOUND,
            )

        tenant = user.tenant
        payload = {
            "status": tenant.status,
            "tenant": {
                "id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug,
                "status": tenant.status,
            },
            "user": {
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active,
            },
        }

        if tenant.status == TenantStatus.PENDING:
            payload["detail"] = (
                "Your application is still pending approval."
            )
        elif tenant.status == TenantStatus.REJECTED:
            payload["detail"] = (
                "Your application was not approved."
            )
        elif not user.is_active:
            payload["detail"] = (
                "Your account is not active. Please contact support."
            )
        elif user.must_change_password and not user.temp_password_revealed:
            temp_password = _mint_temp_password()
            user.set_password(temp_password)
            user.temp_password_revealed = True
            user.save(
                update_fields=[
                    "password",
                    "temp_password_revealed",
                    "updated_at",
                ]
            )
            payload["temp_password"] = temp_password
            payload["detail"] = (
                "Approved! Use this one-time temporary password to log in. "
                "It is shown only once — you must change it right after login."
            )
        elif user.must_change_password:
            payload["detail"] = (
                "Approved. Your temporary password was already issued — "
                "log in with it and change it immediately."
            )
        else:
            payload["detail"] = "Approved. Log in with your password."

        return Response(payload)


class ChangePasswordView(APIView):
    """Authenticated password change; clears the forced-rotation flag."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "Password changed successfully."})

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