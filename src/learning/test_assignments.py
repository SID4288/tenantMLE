from datetime import timedelta

from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone

from accounts.models import User, UserRole
from courses.models import Course
from tenants.models import Tenant, TenantStatus
from .models import Assignment, AssignmentProgress, CourseAssignment


def make_tenant(name, slug):
    now = timezone.now()
    return Tenant.objects.create(
        name=name,
        slug=slug,
        status=TenantStatus.ACTIVE,
        trial_started_at=now - timedelta(days=1),
        trial_ends_at=now + timedelta(days=29),
    )

def make_user(username, email, tenant, role=UserRole.TENANT_USER):
    return User.objects.create_user(
        username=username,
        email=email,
        password="password",
        role=role,
        tenant=tenant,
    )


class AssignmentModelTests(TestCase):
    def setUp(self):
        self.tenant_a = make_tenant("Tenant A", "tenant-a")
        self.tenant_b = make_tenant("Tenant B", "tenant-b")
        self.course_a = Course.objects.create(
            tenant=self.tenant_a, title="Course A"
        )

    def test_assignment_belongs_to_course(self):
        assignment = Assignment.objects.create(
            course=self.course_a,
            title="Read chapter 1",
            description="Intro reading",
            learning_material="https://example.com/ch1",
            task="Summarize the chapter",
            order=1,
        )

        self.assertEqual(assignment.course_id, self.course_a.id)
        self.assertIn(assignment, self.course_a.content_assignments.all())
        self.assertIsNotNone(assignment.created_at)
        self.assertIsNotNone(assignment.updated_at)
        # Tenant is derived through the course — always the same tenant.
        self.assertEqual(assignment.course.tenant_id, self.tenant_a.id)

    def test_assignment_requires_course(self):
        assignment = Assignment(title="Orphan")

        with self.assertRaises(ValidationError):
            assignment.save()

        self.assertEqual(Assignment.objects.count(), 0)

    def test_assignment_requires_title(self):
        assignment = Assignment(course=self.course_a, title="")

        with self.assertRaises(ValidationError):
            assignment.save()

    def test_assignment_ordering_is_deterministic(self):
        for order, title in [(30, "third"), (10, "first"), (20, "second")]:
            Assignment.objects.create(
                course=self.course_a, title=title, order=order
            )

        titles = list(
            Assignment.objects.filter(course=self.course_a).values_list(
                "title", flat=True
            )
        )
        self.assertEqual(titles, ["first", "second", "third"])

    def test_assignment_order_ties_broken_by_id(self):
        first = Assignment.objects.create(
            course=self.course_a, title="tie-a", order=5
        )
        second = Assignment.objects.create(
            course=self.course_a, title="tie-b", order=5
        )

        ids = list(
            Assignment.objects.filter(course=self.course_a).values_list(
                "id", flat=True
            )
        )
        self.assertEqual(ids, [first.id, second.id])

    def test_legacy_course_assignment_still_works(self):
        user = make_user("legacy-user", "legacy@example.com", self.tenant_a)

        enrollment = CourseAssignment.objects.create(
            course=self.course_a, user=user
        )

        self.assertEqual(enrollment.course_id, self.course_a.id)
        self.assertEqual(enrollment.user_id, user.id)


class AssignmentProgressModelTests(TestCase):
    def setUp(self):
        self.tenant_a = make_tenant("Tenant A", "tenant-a")
        self.tenant_b = make_tenant("Tenant B", "tenant-b")
        self.user_a = make_user("user-a", "a@example.com", self.tenant_a)
        self.user_b = make_user("user-b", "b@example.com", self.tenant_b)
        self.course_a = Course.objects.create(
            tenant=self.tenant_a, title="Course A"
        )
        self.course_b = Course.objects.create(
            tenant=self.tenant_b, title="Course B"
        )
        self.assignment_a = Assignment.objects.create(
            course=self.course_a, title="Task A", order=1
        )
        self.assignment_b = Assignment.objects.create(
            course=self.course_b, title="Task B", order=1
        )

    def test_same_tenant_progress_is_allowed(self):
        progress = AssignmentProgress.objects.create(
            assignment=self.assignment_a, user=self.user_a
        )

        self.assertFalse(progress.completed)
        self.assertIsNone(progress.completed_at)
        self.assertIsNotNone(progress.started_at)
        self.assertEqual(
            self.user_a.assignment_progress.get().id, progress.id
        )
        self.assertEqual(
            self.assignment_a.progress_records.get().id, progress.id
        )

    def test_duplicate_progress_is_rejected(self):
        AssignmentProgress.objects.create(
            assignment=self.assignment_a, user=self.user_a
        )

        with self.assertRaises(ValidationError):
            AssignmentProgress.objects.create(
                assignment=self.assignment_a, user=self.user_a
            )

        self.assertEqual(
            AssignmentProgress.objects.filter(
                assignment=self.assignment_a, user=self.user_a
            ).count(),
            1,
        )

    def test_duplicate_progress_rejected_at_database_level(self):
        AssignmentProgress.objects.create(
            assignment=self.assignment_a, user=self.user_a
        )

        # bulk_create skips model validation: the DB constraint is the
        # last line of defense against duplicates.
        with self.assertRaises(IntegrityError):
            AssignmentProgress.objects.bulk_create(
                [
                    AssignmentProgress(
                        assignment=self.assignment_a, user=self.user_a
                    )
                ]
            )

    def test_cross_tenant_progress_is_rejected(self):
        progress = AssignmentProgress(
            assignment=self.assignment_b, user=self.user_a
        )

        with self.assertRaises(ValidationError):
            progress.save()

        self.assertFalse(
            AssignmentProgress.objects.filter(
                assignment=self.assignment_b, user=self.user_a
            ).exists()
        )

    def test_cross_tenant_progress_rejected_in_both_directions(self):
        with self.assertRaises(ValidationError):
            AssignmentProgress(
                assignment=self.assignment_a, user=self.user_b
            ).save()

    def test_tenantless_user_progress_is_rejected(self):
        drifter = User.objects.create_user(
            username="drifter",
            email="drifter@example.com",
            password="password",
            role=UserRole.TENANT_USER,
            tenant=None,
        )

        with self.assertRaises(ValidationError):
            AssignmentProgress(
                assignment=self.assignment_a, user=drifter
            ).save()

    def test_different_users_may_progress_same_assignment(self):
        teammate = make_user("teammate", "mate@example.com", self.tenant_a)

        AssignmentProgress.objects.create(
            assignment=self.assignment_a, user=self.user_a
        )
        AssignmentProgress.objects.create(
            assignment=self.assignment_a, user=teammate
        )

        self.assertEqual(
            AssignmentProgress.objects.filter(
                assignment=self.assignment_a
            ).count(),
            2,
        )
