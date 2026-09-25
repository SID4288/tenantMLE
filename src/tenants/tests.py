from datetime import timedelta
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import User, UserRole
from .models import Tenant, TenantStatus


class TenantLifecycleTests(TestCase):

    def test_trial_active_tenant_remains_active_before_expiration(self):
        now = timezone.now()

        tenant = Tenant.objects.create(
            name="Active Tenant",
            slug="active-tenant",
            status=TenantStatus.TRIAL_ACTIVE,
            trial_started_at=now,
            trial_ends_at=now + timedelta(days=7),
        )

        status = tenant.refresh_status()

        self.assertEqual(status, TenantStatus.TRIAL_ACTIVE)

        tenant.refresh_from_db()
        self.assertEqual(tenant.status, TenantStatus.TRIAL_ACTIVE)

    def test_trial_tenant_expires_after_trial_end(self):
        now = timezone.now()

        tenant = Tenant.objects.create(
            name="Expired Tenant",
            slug="expired-tenant",
            status=TenantStatus.TRIAL_ACTIVE,
            trial_started_at=now - timedelta(days=8),
            trial_ends_at=now - timedelta(days=1),
        )

        status = tenant.refresh_status()

        self.assertEqual(status, TenantStatus.EXPIRED)

        tenant.refresh_from_db()
        self.assertEqual(tenant.status, TenantStatus.EXPIRED)

    def test_tenant_expiring_exactly_now_becomes_expired(self):
        now = timezone.now()

        tenant = Tenant.objects.create(
            name="Boundary Tenant",
            slug="boundary-tenant",
            status=TenantStatus.TRIAL_ACTIVE,
            trial_started_at=now - timedelta(days=7),
            trial_ends_at=now,
        )

        status = tenant.refresh_status()

        self.assertEqual(status, TenantStatus.EXPIRED)

    def test_expired_tenant_does_not_change_back_to_active(self):
        now = timezone.now()

        tenant = Tenant.objects.create(
            name="Already Expired",
            slug="already-expired",
            status=TenantStatus.EXPIRED,
            trial_started_at=now - timedelta(days=10),
            trial_ends_at=now - timedelta(days=3),
        )

        status = tenant.refresh_status()

        self.assertEqual(status, TenantStatus.EXPIRED)

        tenant.refresh_from_db()
        self.assertEqual(tenant.status, TenantStatus.EXPIRED)

    def test_active_tenant_does_not_become_expired(self):
        now = timezone.now()

        tenant = Tenant.objects.create(
            name="Paid Tenant",
            slug="paid-tenant",
            status=TenantStatus.ACTIVE,
            trial_started_at=now - timedelta(days=30),
            trial_ends_at=now - timedelta(days=23),
        )

        status = tenant.refresh_status()

        self.assertEqual(status, TenantStatus.ACTIVE)

        tenant.refresh_from_db()
        self.assertEqual(tenant.status, TenantStatus.ACTIVE)

    def test_expired_tenant_can_be_reactivated(self):
        now = timezone.now()

        tenant = Tenant.objects.create(
            name="Reactivatable Tenant",
            slug="reactivatable-tenant",
            status=TenantStatus.EXPIRED,
            trial_started_at=now - timedelta(days=30),
            trial_ends_at=now - timedelta(days=23),
        )

        status = tenant.reactivate()

        self.assertEqual(status, TenantStatus.ACTIVE)

        tenant.refresh_from_db()
        self.assertEqual(tenant.status, TenantStatus.ACTIVE)

    def test_expiration_preserves_tenant_data(self):
        now = timezone.now()

        tenant = Tenant.objects.create(
            name="Data Tenant",
            slug="data-tenant",
            status=TenantStatus.TRIAL_ACTIVE,
            trial_started_at=now - timedelta(days=8),
            trial_ends_at=now - timedelta(days=1),
        )

        status = tenant.refresh_status()

        self.assertEqual(status, TenantStatus.EXPIRED)

        tenant.refresh_from_db()

        self.assertEqual(tenant.name, "Data Tenant")
        self.assertEqual(tenant.slug, "data-tenant")
        self.assertEqual(tenant.status, TenantStatus.EXPIRED)
class TenantManagementAPITests(APITestCase):

    def setUp(self):
        now = timezone.now()

        self.super_admin = User.objects.create_user(
            username="super-admin",
            email="super-admin@example.com",
            password="test-password",
            role=UserRole.SUPER_ADMIN,
        )

        self.tenant_admin = User.objects.create_user(
            username="tenant-admin",
            email="tenant-admin@example.com",
            password="test-password",
            role=UserRole.TENANT_ADMIN,
            tenant=Tenant.objects.create(
                name="Existing Tenant",
                slug="existing-tenant",
                status=TenantStatus.ACTIVE,
                trial_started_at=now - timedelta(days=30),
                trial_ends_at=now - timedelta(days=23),
            ),
        )

    def test_only_super_admin_can_access_tenant_management(self):
        self.client.force_authenticate(user=self.tenant_admin)

        list_response = self.client.get(reverse("tenant-list"))
        create_response = self.client.post(
            reverse("tenant-list"),
            {
                "name": "Unauthorized",
                "slug": "unauthorized",
            },
        )

        self.assertEqual(
            list_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
        self.assertEqual(
            create_response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_super_admin_can_create_tenant_with_initialized_trial(self):
        self.client.force_authenticate(user=self.super_admin)

        before = timezone.now()

        response = self.client.post(
            reverse("tenant-list"),
            {
                "name": "New Tenant",
                "slug": "new-tenant",
                # Deliberately attempt to spoof lifecycle fields.
                "status": TenantStatus.ACTIVE,
                "trial_started_at": before - timedelta(days=100),
                "trial_ends_at": before - timedelta(days=1),
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )

        tenant = Tenant.objects.get(slug="new-tenant")

        self.assertEqual(
            tenant.status,
            TenantStatus.TRIAL_ACTIVE,
        )

        self.assertGreaterEqual(
            tenant.trial_started_at,
            before,
        )

        self.assertEqual(
            tenant.trial_ends_at - tenant.trial_started_at,
            timedelta(days=30),
        )

    def test_super_admin_can_list_retrieve_and_update_tenant_details(self):
        self.client.force_authenticate(user=self.super_admin)

        tenant = self.tenant_admin.tenant

        list_response = self.client.get(
            reverse("tenant-list")
        )

        retrieve_response = self.client.get(
            reverse("tenant-detail", args=[tenant.id])
        )

        update_response = self.client.patch(
            reverse("tenant-detail", args=[tenant.id]),
            {
                "name": "Updated Tenant",
            },
        )

        self.assertEqual(
            list_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            retrieve_response.status_code,
            status.HTTP_200_OK,
        )

        self.assertEqual(
            update_response.status_code,
            status.HTTP_200_OK,
        )

        tenant.refresh_from_db()

        self.assertEqual(
            tenant.name,
            "Updated Tenant",
        )

        # Normal tenant updates must not arbitrarily change lifecycle state.
        self.assertEqual(
            tenant.status,
            TenantStatus.ACTIVE,
        )
