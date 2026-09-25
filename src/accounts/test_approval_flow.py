from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User, UserRole
from tenants.models import Tenant, TenantStatus


def apply_organization(client, org="Flow Org", admin="flow_admin",
                       email="flow@example.com"):
    return client.post(
        reverse("tenant_application"),
        {
            "organization_name": org,
            "admin_name": admin,
            "admin_email": email,
        },
    )


def make_super_admin():
    return User.objects.create_user(
        username="flow-superadmin",
        email="flow-superadmin@example.com",
        password="superpass1",
        role=UserRole.SUPER_ADMIN,
    )


class TenantApprovalTests(APITestCase):
    def setUp(self):
        self.super_admin = make_super_admin()
        self.client.force_authenticate(user=self.super_admin)

    def test_super_admin_can_approve_pending_tenant(self):
        self.client.force_authenticate(user=None)
        apply_response = apply_organization(self.client)
        tenant_id = apply_response.data["tenant"]["id"]

        self.client.force_authenticate(user=self.super_admin)
        before = timezone.now()
        response = self.client.post(
            reverse("tenant-approve", args=[tenant_id])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], TenantStatus.TRIAL_ACTIVE)
        self.assertEqual(response.data["admin"]["username"], "flow_admin")

        tenant = Tenant.objects.get(id=tenant_id)
        self.assertEqual(tenant.status, TenantStatus.TRIAL_ACTIVE)
        self.assertGreaterEqual(tenant.trial_started_at, before)
        self.assertEqual(
            tenant.trial_ends_at - tenant.trial_started_at,
            timedelta(days=30),
        )

        admin = User.objects.get(username="flow_admin")
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.must_change_password)
        self.assertFalse(admin.temp_password_revealed)
        # Still no usable password: it is minted at status check.
        self.assertFalse(admin.has_usable_password())

    def test_approve_rejects_non_pending_tenant(self):
        now = timezone.now()
        tenant = Tenant.objects.create(
            name="Live Org",
            slug="live-org",
            status=TenantStatus.ACTIVE,
            trial_started_at=now - timedelta(days=1),
            trial_ends_at=now + timedelta(days=29),
        )

        response = self.client.post(reverse("tenant-approve", args=[tenant.id]))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_approve_requires_pending_admin(self):
        now = timezone.now()
        tenant = Tenant.objects.create(
            name="Lonely Org",
            slug="lonely-org",
            status=TenantStatus.PENDING,
            trial_started_at=now,
            trial_ends_at=now + timedelta(days=30),
        )

        response = self.client.post(reverse("tenant-approve", args=[tenant.id]))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        tenant.refresh_from_db()
        self.assertEqual(tenant.status, TenantStatus.PENDING)

    def test_non_super_admin_cannot_approve(self):
        apply_response = apply_organization(self.client)
        tenant_id = apply_response.data["tenant"]["id"]

        tenant_admin = User.objects.create_user(
            username="flow-tenant-admin",
            email="flow-tenant-admin@example.com",
            password="tenantpass1",
            role=UserRole.TENANT_ADMIN,
        )
        self.client.force_authenticate(user=tenant_admin)
        response = self.client.post(
            reverse("tenant-approve", args=[tenant_id])
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_approve(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(reverse("tenant-approve", args=[1]))

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_super_admin_can_reject_pending_tenant(self):
        self.client.force_authenticate(user=None)
        apply_response = apply_organization(self.client)
        tenant_id = apply_response.data["tenant"]["id"]

        self.client.force_authenticate(user=self.super_admin)
        response = self.client.post(
            reverse("tenant-reject", args=[tenant_id])
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], TenantStatus.REJECTED)

        admin = User.objects.get(username="flow_admin")
        self.assertFalse(admin.is_active)

    def test_reject_rejects_non_pending_tenant(self):
        now = timezone.now()
        tenant = Tenant.objects.create(
            name="Live Org 2",
            slug="live-org-2",
            status=TenantStatus.ACTIVE,
            trial_started_at=now - timedelta(days=1),
            trial_ends_at=now + timedelta(days=29),
        )

        response = self.client.post(reverse("tenant-reject", args=[tenant.id]))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class ApplicationStatusTests(APITestCase):
    def setUp(self):
        self.super_admin = make_super_admin()
        self.url = reverse("application_status")

    def approve_flow_org(self, org="Status Org", admin="status_admin",
                         email="status@example.com"):
        self.client.force_authenticate(user=None)
        apply_response = apply_organization(
            self.client, org=org, admin=admin, email=email
        )
        tenant_id = apply_response.data["tenant"]["id"]
        self.client.force_authenticate(user=self.super_admin)
        self.client.post(reverse("tenant-approve", args=[tenant_id]))
        self.client.force_authenticate(user=None)

    def test_unknown_email_returns_404(self):
        response = self.client.post(
            self.url, {"admin_email": "nobody@example.com"}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_missing_email_returns_400(self):
        response = self.client.post(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_pending_application_reports_pending_without_password(self):
        apply_organization(self.client)

        response = self.client.post(
            self.url, {"admin_email": "flow@example.com"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], TenantStatus.PENDING)
        self.assertNotIn("temp_password", response.data)

    def test_rejected_application_reports_rejected(self):
        apply_response = apply_organization(self.client)
        tenant_id = apply_response.data["tenant"]["id"]
        self.client.force_authenticate(user=self.super_admin)
        self.client.post(reverse("tenant-reject", args=[tenant_id]))
        self.client.force_authenticate(user=None)

        response = self.client.post(
            self.url, {"admin_email": "flow@example.com"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], TenantStatus.REJECTED)
        self.assertNotIn("temp_password", response.data)

    def test_first_status_check_after_approval_reveals_temp_password_once(self):
        self.approve_flow_org()

        first = self.client.post(
            self.url, {"admin_email": "status@example.com"}
        )
        self.assertEqual(first.status_code, status.HTTP_200_OK)
        self.assertIn("temp_password", first.data)
        temp_password = first.data["temp_password"]
        self.assertGreaterEqual(len(temp_password), 8)

        # The minted password actually logs in.
        token_response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "status_admin", "password": temp_password},
        )
        self.assertEqual(token_response.status_code, status.HTTP_200_OK)

        # Second check never reveals it again.
        second = self.client.post(
            self.url, {"admin_email": "status@example.com"}
        )
        self.assertEqual(second.status_code, status.HTTP_200_OK)
        self.assertNotIn("temp_password", second.data)


class ChangePasswordTests(APITestCase):
    def setUp(self):
        self.super_admin = make_super_admin()
        self.url = reverse("change_password")

    def approved_admin_with_temp(self, org="Pw Org", admin="pw_admin",
                                 email="pw@example.com"):
        self.client.force_authenticate(user=None)
        apply_response = apply_organization(
            self.client, org=org, admin=admin, email=email
        )
        tenant_id = apply_response.data["tenant"]["id"]
        self.client.force_authenticate(user=self.super_admin)
        self.client.post(reverse("tenant-approve", args=[tenant_id]))
        self.client.force_authenticate(user=None)
        status_response = self.client.post(
            reverse("application_status"), {"admin_email": email}
        )
        return status_response.data["temp_password"]

    def test_unauthenticated_change_is_rejected(self):
        response = self.client.post(
            self.url,
            {"current_password": "x", "new_password": "newstrong1"},
        )

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )

    def test_wrong_current_password_is_rejected(self):
        temp = self.approved_admin_with_temp()
        token = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "pw_admin", "password": temp},
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.post(
            self.url,
            {"current_password": "wrong-temp", "new_password": "newstrong1"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_short_new_password_is_rejected(self):
        temp = self.approved_admin_with_temp()
        token = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "pw_admin", "password": temp},
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.post(
            self.url, {"current_password": temp, "new_password": "short"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_exposes_forced_rotation_flag(self):
        temp = self.approved_admin_with_temp()
        token = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "pw_admin", "password": temp},
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = self.client.get(reverse("me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["must_change_password"])

    def test_full_rotation_flow(self):
        temp = self.approved_admin_with_temp(
            org="Full Org", admin="full_admin", email="full@example.com"
        )
        token = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "full_admin", "password": temp},
        ).data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        change = self.client.post(
            self.url,
            {"current_password": temp, "new_password": "brandnew99"},
        )
        self.assertEqual(change.status_code, status.HTTP_200_OK)

        me = self.client.get(reverse("me"))
        self.assertFalse(me.data["must_change_password"])

        status_check = self.client.post(
            reverse("application_status"),
            {"admin_email": "full@example.com"},
        )
        self.assertNotIn("temp_password", status_check.data)

        self.client.credentials()
        old_login = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "full_admin", "password": temp},
        )
        self.assertEqual(old_login.status_code, status.HTTP_401_UNAUTHORIZED)

        new_login = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "full_admin", "password": "brandnew99"},
        )
        self.assertEqual(new_login.status_code, status.HTTP_200_OK)
