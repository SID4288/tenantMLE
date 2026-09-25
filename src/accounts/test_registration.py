from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User, UserRole
from tenants.models import Tenant, TenantStatus


def make_tenant(name, slug, tenant_status):
    now = timezone.now()
    return Tenant.objects.create(
        name=name,
        slug=slug,
        status=tenant_status,
        trial_started_at=now - timedelta(days=1),
        trial_ends_at=now + timedelta(days=29),
    )


class TenantUserRegistrationTests(APITestCase):
    def setUp(self):
        self.active_tenant = make_tenant(
            "Joinable Tenant", "joinable-tenant", TenantStatus.ACTIVE
        )
        self.trial_tenant = make_tenant(
            "Trial Tenant", "trial-tenant", TenantStatus.TRIAL_ACTIVE
        )
        self.pending_tenant = make_tenant(
            "Pending Tenant", "pending-tenant", TenantStatus.PENDING
        )
        self.expired_tenant = make_tenant(
            "Expired Tenant", "expired-tenant", TenantStatus.EXPIRED
        )
        self.url = reverse("register")

    def test_register_creates_tenant_user_with_hashed_password(self):
        response = self.client.post(
            self.url,
            {
                "username": "new-learner",
                "email": "new-learner@example.com",
                "password": "strongpass1",
                "tenant": self.active_tenant.id,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], UserRole.TENANT_USER)
        self.assertEqual(response.data["tenant"], self.active_tenant.id)

        user = User.objects.get(username="new-learner")
        self.assertEqual(user.role, UserRole.TENANT_USER)
        self.assertEqual(user.tenant_id, self.active_tenant.id)
        self.assertTrue(user.is_active)
        # Password must be hashed, never stored raw.
        self.assertNotEqual(user.password, "strongpass1")
        self.assertTrue(user.check_password("strongpass1"))

    def test_registered_user_can_log_in(self):
        self.client.post(
            self.url,
            {
                "username": "login-learner",
                "email": "login-learner@example.com",
                "password": "strongpass1",
                "tenant": self.trial_tenant.id,
            },
        )

        token_response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "login-learner", "password": "strongpass1"},
        )

        self.assertEqual(token_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", token_response.data)

    def test_register_ignores_spoofed_admin_role(self):
        response = self.client.post(
            self.url,
            {
                "username": "sneaky",
                "email": "sneaky@example.com",
                "password": "strongpass1",
                "tenant": self.active_tenant.id,
                "role": UserRole.TENANT_ADMIN,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username="sneaky")
        self.assertEqual(user.role, UserRole.TENANT_USER)

    def test_register_rejects_nonexistent_tenant(self):
        response = self.client.post(
            self.url,
            {
                "username": "orphan",
                "email": "orphan@example.com",
                "password": "strongpass1",
                "tenant": 999999,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="orphan").exists())

    def test_register_rejects_pending_tenant(self):
        response = self.client.post(
            self.url,
            {
                "username": "early-bird",
                "email": "early-bird@example.com",
                "password": "strongpass1",
                "tenant": self.pending_tenant.id,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="early-bird").exists())

    def test_register_rejects_expired_tenant(self):
        response = self.client.post(
            self.url,
            {
                "username": "late-comer",
                "email": "late-comer@example.com",
                "password": "strongpass1",
                "tenant": self.expired_tenant.id,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="late-comer").exists())

    def test_register_rejects_duplicate_username_and_email(self):
        User.objects.create_user(
            username="taken",
            email="taken@example.com",
            password="strongpass1",
            role=UserRole.TENANT_USER,
            tenant=self.active_tenant,
        )

        for payload in (
            {
                "username": "taken",
                "email": "other@example.com",
                "password": "strongpass1",
                "tenant": self.active_tenant.id,
            },
            {
                "username": "other",
                "email": "taken@example.com",
                "password": "strongpass1",
                "tenant": self.active_tenant.id,
            },
        ):
            response = self.client.post(self.url, payload)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_requires_password(self):
        response = self.client.post(
            self.url,
            {
                "username": "nopass",
                "email": "nopass@example.com",
                "tenant": self.active_tenant.id,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="nopass").exists())


class TenantApplicationTests(APITestCase):
    def setUp(self):
        self.url = reverse("tenant_application")

    def test_apply_creates_pending_tenant_and_inactive_admin(self):
        response = self.client.post(
            self.url,
            {
                "organization_name": "Acme Academy",
                "admin_name": "acme_admin",
                "admin_email": "admin@acme.example",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["tenant"]["status"], TenantStatus.PENDING)
        self.assertEqual(response.data["tenant"]["name"], "Acme Academy")
        self.assertEqual(response.data["user"]["role"], UserRole.TENANT_ADMIN)
        self.assertFalse(response.data["user"]["is_active"])

        tenant = Tenant.objects.get(slug=response.data["tenant"]["slug"])
        self.assertEqual(tenant.status, TenantStatus.PENDING)

        user = User.objects.get(username="acme_admin")
        self.assertEqual(user.role, UserRole.TENANT_ADMIN)
        self.assertEqual(user.tenant_id, tenant.id)
        self.assertFalse(user.is_active)
        # No usable password may exist before approval.
        self.assertFalse(user.has_usable_password())

    def test_applicant_cannot_choose_role(self):
        response = self.client.post(
            self.url,
            {
                "organization_name": "Role Gamers",
                "admin_name": "role_gamer",
                "admin_email": "gamer@example.com",
                "role": UserRole.SUPER_ADMIN,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        user = User.objects.get(username="role_gamer")
        self.assertEqual(user.role, UserRole.TENANT_ADMIN)

    def test_pending_admin_cannot_log_in(self):
        self.client.post(
            self.url,
            {
                "organization_name": "Locked Org",
                "admin_name": "locked_admin",
                "admin_email": "locked@example.com",
            },
        )

        token_response = self.client.post(
            reverse("token_obtain_pair"),
            {"username": "locked_admin", "password": "anything123"},
        )

        self.assertEqual(token_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_duplicate_organization_name_gets_unique_slug(self):
        first = self.client.post(
            self.url,
            {
                "organization_name": "Same Name",
                "admin_name": "admin_one",
                "admin_email": "one@example.com",
            },
        )
        second = self.client.post(
            self.url,
            {
                "organization_name": "Same Name",
                "admin_name": "admin_two",
                "admin_email": "two@example.com",
            },
        )

        self.assertEqual(first.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(
            first.data["tenant"]["slug"], second.data["tenant"]["slug"]
        )
        self.assertEqual(
            Tenant.objects.filter(name="Same Name").count(), 2
        )

    def test_duplicate_admin_identity_creates_nothing(self):
        tenants_before = Tenant.objects.count()

        self.client.post(
            self.url,
            {
                "organization_name": "First Org",
                "admin_name": "dup_admin",
                "admin_email": "dup@example.com",
            },
        )

        for payload in (
            {
                "organization_name": "Second Org",
                "admin_name": "dup_admin",
                "admin_email": "fresh@example.com",
            },
            {
                "organization_name": "Third Org",
                "admin_name": "fresh_admin",
                "admin_email": "dup@example.com",
            },
        ):
            response = self.client.post(self.url, payload)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Failed applications must not leave orphan tenants behind.
        self.assertEqual(Tenant.objects.count(), tenants_before + 1)

    def test_apply_rejects_blank_organization_name(self):
        response = self.client.post(
            self.url,
            {
                "organization_name": "   ",
                "admin_name": "blank_admin",
                "admin_email": "blank@example.com",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="blank_admin").exists())
