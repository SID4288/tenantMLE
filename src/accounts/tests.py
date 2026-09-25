from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from .models import User, UserRole
from datetime import timedelta

from django.utils import timezone
from tenants.models import Tenant, TenantStatus

class SuperAdminTestViewTests(APITestCase):
    def test_super_admin_can_access_endpoint(self):
        user = User.objects.create_user(
            username="super-admin",
            email="super-admin@example.com",
            password="password",
            role=UserRole.SUPER_ADMIN,
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(reverse("super_admin_test"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["role"], UserRole.SUPER_ADMIN)

    def test_non_super_admin_is_forbidden(self):
        user = User.objects.create_user(
            username="tenant-user",
            email="tenant-user@example.com",
            password="password",
            role=UserRole.TENANT_USER,
        )
        self.client.force_authenticate(user=user)

        response = self.client.get(reverse("super_admin_test"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_is_rejected(self):
        response = self.client.get(reverse("super_admin_test"))

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )
class JWTAuthenticationTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="jwt-user",
            email="jwt@example.com",
            password="password123",
            role=UserRole.TENANT_USER,
        )

    def test_user_can_obtain_jwt_tokens(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "username": "jwt-user",
                "password": "password123",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_invalid_credentials_are_rejected(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "username": "jwt-user",
                "password": "wrong-password",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_token_can_authenticate_user(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "username": "jwt-user",
                "password": "password123",
            },
        )

        access_token = response.data["access"]

        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {access_token}"
        )

        response = self.client.get(reverse("me"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "jwt@example.com")
        self.assertEqual(response.data["role"], UserRole.TENANT_USER)

    def test_refresh_token_returns_new_access_token(self):
        response = self.client.post(
            reverse("token_obtain_pair"),
            {
                "username": "jwt-user",
                "password": "password123",
            },
        )

        refresh_token = response.data["refresh"]

        response = self.client.post(
            reverse("token_refresh"),
            {"refresh": refresh_token},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_protected_endpoint_rejects_unauthenticated_request(self):
        response = self.client.get(reverse("me"))

        self.assertIn(
            response.status_code,
            (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN),
        )


class UserManagementTests(APITestCase):
    def setUp(self):
        now = timezone.now()

        self.tenant_a = Tenant.objects.create(
            name="Tenant A",
            slug="tenant-a",
            status=TenantStatus.ACTIVE,
            trial_started_at=now - timedelta(days=30),
            trial_ends_at=now - timedelta(days=23),
        )

        self.tenant_b = Tenant.objects.create(
            name="Tenant B",
            slug="tenant-b",
            status=TenantStatus.ACTIVE,
            trial_started_at=now - timedelta(days=30),
            trial_ends_at=now - timedelta(days=23),
        )

        self.tenant_admin = User.objects.create_user(
            username="tenant-admin",
            email="admin@a.com",
            password="password",
            role=UserRole.TENANT_ADMIN,
            tenant=self.tenant_a,
        )

        self.tenant_a_user = User.objects.create_user(
            username="user-a",
            email="user-a@a.com",
            password="password",
            role=UserRole.TENANT_USER,
            tenant=self.tenant_a,
        )

        self.tenant_b_user = User.objects.create_user(
            username="user-b",
            email="user-b@b.com",
            password="password",
            role=UserRole.TENANT_USER,
            tenant=self.tenant_b,
        )

    def test_tenant_admin_can_list_users_from_own_tenant(self):
        self.client.force_authenticate(user=self.tenant_admin)

        response = self.client.get(reverse("user-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = {user["id"] for user in response.data}

        self.assertIn(self.tenant_a_user.id, returned_ids)
        self.assertNotIn(self.tenant_b_user.id, returned_ids)

    def test_tenant_admin_can_create_tenant_user(self):
        self.client.force_authenticate(user=self.tenant_admin)

        response = self.client.post(
            reverse("user-list"),
            {
                "username": "new-user",
                "email": "new-user@a.com",
                "password": "password123",
                "role": UserRole.TENANT_USER,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        created_user = User.objects.get(username="new-user")

        self.assertEqual(created_user.tenant_id, self.tenant_a.id)
        self.assertEqual(created_user.role, UserRole.TENANT_USER)

    def test_platform_admin_cannot_create_tenant_user_without_tenant(self):
        platform_admin = User.objects.create_user(
            username="platform-admin-create",
            email="platform-admin-create@example.com",
            role=UserRole.ADMIN,
        )
        self.client.force_authenticate(user=platform_admin)

        response = self.client.post(
            reverse("user-list"),
            {
                "username": "orphan-user",
                "email": "orphan-user@example.com",
                "password": "password123",
                "role": UserRole.TENANT_USER,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="orphan-user").exists())

    def test_tenant_admin_cannot_create_admin(self):
        self.client.force_authenticate(user=self.tenant_admin)

        response = self.client.post(
            reverse("user-list"),
            {
                "username": "new-admin",
                "email": "new-admin@a.com",
                "password": "password123",
                "role": UserRole.TENANT_ADMIN,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_tenant_admin_cannot_access_other_tenant_user(self):
        self.client.force_authenticate(user=self.tenant_admin)

        response = self.client.get(
            reverse("user-detail", kwargs={"pk": self.tenant_b_user.id})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_tenant_user_cannot_manage_users(self):
        self.client.force_authenticate(user=self.tenant_a_user)

        response = self.client.get(reverse("user-list"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tenant_admin_cannot_promote_tenant_user(self):
        self.client.force_authenticate(user=self.tenant_admin)

        response = self.client.patch(
            reverse(
                "user-detail",
                kwargs={"pk": self.tenant_a_user.id},
            ),
            {
                "role": UserRole.ADMIN,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

        self.tenant_a_user.refresh_from_db()

        self.assertEqual(
            self.tenant_a_user.role,
            UserRole.TENANT_USER,
        )

    def test_admin_cannot_promote_user_to_super_admin(self):
        platform_admin = User.objects.create_user(
            username="platform-admin",
            email="platform-admin@example.com",
            role=UserRole.ADMIN,
        )
        self.client.force_authenticate(user=platform_admin)

        response = self.client.patch(
            reverse(
                "user-detail",
                kwargs={"pk": self.tenant_a_user.id},
            ),
            {"role": UserRole.SUPER_ADMIN},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.tenant_a_user.refresh_from_db()
        self.assertEqual(self.tenant_a_user.role, UserRole.TENANT_USER)

    def test_expired_tenant_admin_cannot_manage_users(self):
        self.tenant_a.status = TenantStatus.EXPIRED
        self.tenant_a.save()
        self.client.force_authenticate(user=self.tenant_admin)

        responses = [
            self.client.get(reverse("user-list")),
            self.client.post(
                reverse("user-list"),
                {
                    "username": "expired-user",
                    "email": "expired-user@example.com",
                    "password": "password123",
                    "role": UserRole.TENANT_USER,
                },
            ),
            self.client.patch(
                reverse(
                    "user-detail",
                    kwargs={"pk": self.tenant_a_user.id},
                ),
                {"email": "changed@example.com"},
            ),
            self.client.delete(
                reverse(
                    "user-detail",
                    kwargs={"pk": self.tenant_a_user.id},
                )
            ),
        ]

        for response in responses:
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.assertTrue(
            User.objects.filter(id=self.tenant_a_user.id).exists()
        )

    def test_super_viewer_can_list_users(self):
        super_viewer = User.objects.create_user(
            username="super-viewer",
            email="viewer@example.com",
            password="password",
            role=UserRole.SUPER_VIEWER,
        )

        self.client.force_authenticate(user=super_viewer)

        response = self.client.get(reverse("user-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)


    def test_super_viewer_cannot_create_user(self):
        super_viewer = User.objects.create_user(
            username="super-viewer",
            email="viewer@example.com",
            password="password",
            role=UserRole.SUPER_VIEWER,
        )

        self.client.force_authenticate(user=super_viewer)

        response = self.client.post(
            reverse("user-list"),
            {
                "username": "new-user",
                "email": "new@example.com",
                "password": "password123",
                "role": UserRole.TENANT_USER,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_super_viewer_cannot_update_user(self):
        super_viewer = User.objects.create_user(
            username="super-viewer",
            email="viewer@example.com",
            password="password",
            role=UserRole.SUPER_VIEWER,
        )

        self.client.force_authenticate(user=super_viewer)

        response = self.client.patch(
            reverse(
                "user-detail",
                kwargs={"pk": self.tenant_a_user.id},
            ),
            {"email": "changed@example.com"},
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


    def test_super_viewer_cannot_delete_user(self):
        super_viewer = User.objects.create_user(
            username="super-viewer",
            email="viewer@example.com",
            password="password",
            role=UserRole.SUPER_VIEWER,
        )

        self.client.force_authenticate(user=super_viewer)

        response = self.client.delete(
            reverse(
                "user-detail",
                kwargs={"pk": self.tenant_a_user.id},
            )
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)