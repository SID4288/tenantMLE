from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from accounts.models import User, UserRole
from courses.models import Course
from tenants.models import Tenant, TenantStatus
from .models import CourseAssignment, LearningProgress


class LearningAPITests(APITestCase):

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
        self.user_a2 = User.objects.create_user(
            username="user-a2",
            email="user-a2@example.com",
            password="password",
            role=UserRole.TENANT_USER,
            tenant=self.tenant_a,
        )
        self.user_b = User.objects.create_user(
            username="user-b",
            email="user-b@example.com",
            password="password",
            role=UserRole.TENANT_USER,
            tenant=self.tenant_b,
        )

        self.course_a = Course.objects.create(
            tenant=self.tenant_a,
            title="Tenant A Course",
        )

        self.course_b = Course.objects.create(
            tenant=self.tenant_b,
            title="Tenant B Course",
        )

        self.assignment_a = CourseAssignment.objects.create(
            course=self.course_a,
            user=self.user_a,
        )
        self.assignment_a2 = CourseAssignment.objects.create(
            course=self.course_a,
            user=self.user_a2,
        )
        self.assignment_b = CourseAssignment.objects.create(
            course=self.course_b,
            user=self.user_b,
        )

        self.progress_a = LearningProgress.objects.create(
            assignment=self.assignment_a,
            progress_percentage=0,
        )
        self.progress_a2 = LearningProgress.objects.create(
            assignment=self.assignment_a2,
            progress_percentage=25,
        )
        self.progress_b = LearningProgress.objects.create(
            assignment=self.assignment_b,
            progress_percentage=50,
        )

    def test_tenant_admin_can_assign_course_to_tenant_user(self):
        self.client.force_authenticate(user=self.admin_a)

        response = self.client.post(
            reverse("assignment-list"),
            {
                "course": self.course_a.id,
                "user": self.user_a.id,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertTrue(
            CourseAssignment.objects.filter(
                course=self.course_a,
                user=self.user_a,
            ).exists()
        )

        assignment = CourseAssignment.objects.order_by("-id").first()

        self.assertTrue(
            LearningProgress.objects.filter(
                assignment=assignment
            ).exists()
        )

    def test_tenant_admin_cannot_assign_other_tenant_course(self):
        self.client.force_authenticate(user=self.admin_a)

        response = self.client.post(
            reverse("assignment-list"),
            {
                "course": self.course_b.id,
                "user": self.user_a.id,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_course_cannot_be_assigned_to_user_from_different_tenant(self):
        self.client.force_authenticate(user=self.admin_a)

        response = self.client.post(
            reverse("assignment-list"),
            {
                "course": self.course_a.id,
                "user": self.user_b.id,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_tenant_user_can_only_see_own_assignments(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(
            reverse("assignment-list")
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        returned_ids = [
            assignment["id"]
            for assignment in response.data
        ]

        self.assertIn(self.assignment_a.id, returned_ids)
        self.assertNotIn(self.assignment_b.id, returned_ids)

    def test_tenant_user_cannot_access_other_tenant_assignment(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(
            reverse(
                "assignment-detail",
                args=[self.assignment_b.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_tenant_user_can_update_own_progress(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.patch(
            reverse(
                "progress-detail",
                args=[self.progress_a.id],
            ),
            {
                "progress_percentage": 50,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.progress_a.refresh_from_db()

        self.assertEqual(
            self.progress_a.progress_percentage,
            50,
        )
    def test_tenant_user_cannot_create_assignment(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.post(
            reverse("assignment-list"),
            {
                "course": self.course_a.id,
                "user": self.user_a.id,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
    def test_progress_reaches_100_percent(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.patch(
            reverse(
                "progress-detail",
                args=[self.progress_a.id],
            ),
            {
                "progress_percentage": 100,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.progress_a.refresh_from_db()

        self.assertEqual(
            self.progress_a.progress_percentage,
            100,
        )

        self.assertIsNotNone(
            self.progress_a.completed_at
        )

    def test_progress_cannot_exceed_100(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.patch(
            reverse(
                "progress-detail",
                args=[self.progress_a.id],
            ),
            {
                "progress_percentage": 101,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
    def test_tenant_user_cannot_update_other_tenant_progress(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.patch(
            reverse(
                "progress-detail",
                args=[self.progress_b.id],
            ),
            {
                "progress_percentage": 100,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )
    def test_tenant_user_cannot_access_other_tenant_progress(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(
            reverse(
                "progress-detail",
                args=[self.progress_b.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    def test_expired_tenant_cannot_access_learning(self):
        self.tenant_a.status = TenantStatus.EXPIRED
        self.tenant_a.save()

        self.client.force_authenticate(user=self.user_a)

        response = self.client.get(
            reverse("assignment-list")
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_tenant_user_cannot_delete_own_progress(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.delete(
            reverse(
                "progress-detail",
                args=[self.progress_a.id],
            )
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )
    def test_tenant_user_cannot_update_another_users_progress(self):
        self.client.force_authenticate(user=self.user_a)

        response = self.client.patch(
            reverse(
                "progress-detail",
                args=[self.progress_a2.id],
            ),
            {
                "progress_percentage": 100,
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )