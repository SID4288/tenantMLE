from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

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