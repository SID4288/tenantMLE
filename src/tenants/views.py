from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import APIView, action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from accounts.models import UserRole
from accounts.permissions import IsSuperAdmin
from .models import Tenant, TenantStatus
from .serializers import TenantSerializer


class TenantViewSet(ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]

    @action(detail=True, methods=["post"], url_path="approve")
    def approve(self, request, pk=None):
        """Approve a PENDING organization: start its trial and activate
        its admin (who then collects a one-time temp password via the
        application-status endpoint)."""
        tenant = self.get_object()
        if tenant.status != TenantStatus.PENDING:
            return Response(
                {"detail": "Only PENDING tenants can be approved."},
                status=400,
            )
        admin = tenant.users.filter(
            role=UserRole.TENANT_ADMIN, is_active=False
        ).first()
        if admin is None:
            return Response(
                {"detail": "No pending tenant admin found for this tenant."},
                status=400,
            )
        with transaction.atomic():
            now = timezone.now()
            tenant.status = TenantStatus.TRIAL_ACTIVE
            tenant.trial_started_at = now
            tenant.trial_ends_at = now + timedelta(days=30)
            tenant.save(
                update_fields=[
                    "status",
                    "trial_started_at",
                    "trial_ends_at",
                    "updated_at",
                ]
            )
            admin.is_active = True
            admin.must_change_password = True
            admin.temp_password_revealed = False
            admin.save(
                update_fields=[
                    "is_active",
                    "must_change_password",
                    "temp_password_revealed",
                    "updated_at",
                ]
            )
        return Response(
            {
                "id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug,
                "status": tenant.status,
                "admin": {
                    "username": admin.username,
                    "email": admin.email,
                },
            }
        )

    @action(detail=True, methods=["post"], url_path="reject")
    def reject(self, request, pk=None):
        """Reject a PENDING organization; its admin stays inactive."""
        tenant = self.get_object()
        if tenant.status != TenantStatus.PENDING:
            return Response(
                {"detail": "Only PENDING tenants can be rejected."},
                status=400,
            )
        tenant.status = TenantStatus.REJECTED
        tenant.save(update_fields=["status", "updated_at"])
        return Response(
            {
                "id": tenant.id,
                "name": tenant.name,
                "slug": tenant.slug,
                "status": tenant.status,
            }
        )


class PublicTenantListView(APIView):
    """Anonymous list of tenants open for self-registration.

    Only joinable tenants (TRIAL_ACTIVE / ACTIVE) are exposed, with the
    minimal fields the registration form needs. PENDING and EXPIRED
    tenants are never listed.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        tenants = (
            Tenant.objects.filter(
                status__in=[TenantStatus.TRIAL_ACTIVE, TenantStatus.ACTIVE]
            )
            .order_by("name")
            .values("id", "name", "slug")
        )
        return Response(list(tenants))
