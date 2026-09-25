from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User, UserRole
from tenants.models import Tenant, TenantStatus
from .models import Course


class CourseAPITests(APITestCase):

    def setUp(self):
        now = timezone.now()

        self.tenant_a = Tenant.objects.create(
            name="Tenant A",
            slug="tenant-a",
            status=TenantStatus.TRIAL_ACTIVE,
            trial_started_at=now,
            trial_ends_at=now + timedelta(days=30),
        )

        self.tenant_b = Tenant.objects.create(
            name="Tenant B",
            slug="tenant-b",
            status=TenantStatus.TRIAL_ACTIVE,
            trial_started_at=now,
            trial_ends_at=now + timedelta(days=30),
        )

        self.admin_a = User.objects.create_user(
            username="admin-a",
            email="admin-a@example.com",
            password="password",
            role=UserRole.TENANT_ADMIN,
            tenant=self.tenant_a,
        )

        self.user_a = User.objects.create_user(
            username="user-a",
            email="user-a@example.com",
            password="password",
            role=UserRole.TENANT_USER,
            tenant=self.tenant_a,
        )

        self.admin_b = User.objects.create_user(
            username="admin-b",
            email="admin-b@example.com",
            password="password",
            role=UserRole.TENANT_ADMIN,
            tenant=self.tenant_b,
        )

        self.course_a = Course.objects.create(
            tenant=self.tenant_a,
            title="Tenant A Course",
            description="Course for tenant A",
        )

        self.course_b = Course.objects.create(
            tenant=self.tenant_b,
            title="Tenant B Course",
            description="Course for tenant B",
        )

    def test_tenant_admin_can_create_course(self):
        self.client.force_authenticate(user=self.admin_a)

        response = self.client.post(
            reverse("course-list"),
            {
                "title": "New Course",
                "description": "New course description",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        course = Course.objects.get(title="New Course")

        self.assertEqual(course.tenant_id, self.tenant_a.id)

    def test_tenant_user_cannot_create_course(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.post(
            reverse("course-list"),
            {
                "title": "Unauthorized Course",
                "description": "Should not be created",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_tenant_user_can_see_only_own_tenant_courses(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(reverse("course-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = [course["id"] for course in response.data]

        self.assertIn(self.course_a.id, returned_ids)
        self.assertNotIn(self.course_b.id, returned_ids)

    def test_tenant_admin_cannot_access_other_tenant_course(self):
        self.client.force_authenticate(user=self.admin_a)

        response = self.client.get(
            reverse("course-detail", args=[self.course_b.id])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_tenant_user_cannot_access_other_tenant_course(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(
            reverse("course-detail", args=[self.course_b.id])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_tenant_admin_can_update_own_course(self):
        self.client.force_authenticate(user=self.admin_a)

        response = self.client.patch(
            reverse("course-detail", args=[self.course_a.id]),
            {"title": "Updated Course"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.course_a.refresh_from_db()
        self.assertEqual(self.course_a.title, "Updated Course")

    def test_tenant_admin_cannot_delete_other_tenant_course(self):
        self.client.force_authenticate(user=self.admin_a)

        response = self.client.delete(
            reverse("course-detail", args=[self.course_b.id])
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        self.assertTrue(
            Course.objects.filter(id=self.course_b.id).exists()
        )

    def test_expired_tenant_cannot_access_courses(self):
        self.tenant_a.status = TenantStatus.EXPIRED
        self.tenant_a.save()

        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(reverse("course-list"))

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)