from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User, UserRole


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
