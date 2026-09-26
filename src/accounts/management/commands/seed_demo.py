from datetime import timedelta

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.models import User, UserRole
from courses.models import Course
from learning.models import CourseAssignment, LearningProgress
from tenants.models import Tenant, TenantStatus


DEMO_PASSWORD = "Testpassword123!"


class Command(BaseCommand):
    help = "Create or update the local demo tenant, users, course, and progress."

    @transaction.atomic
    def handle(self, *args, **options):
        now = timezone.now()
        tenant, _ = Tenant.objects.update_or_create(
            slug="tenant-a",
            defaults={
                "name": "Tenant A",
                "status": TenantStatus.ACTIVE,
                "trial_started_at": now,
                "trial_ends_at": now + timedelta(days=30),
            },
        )

        demo_users = [
            ("superadmin", "superadmin@example.com", UserRole.SUPER_ADMIN, None),
            ("platformadmin", "platformadmin@example.com", UserRole.ADMIN, None),
            ("superviewer", "superviewer@example.com", UserRole.SUPER_VIEWER, None),
            ("tenant_a_admin", "tenant_a_admin@example.com", UserRole.TENANT_ADMIN, tenant),
            ("tenant_a_user1", "tenant_a_user1@example.com", UserRole.TENANT_USER, tenant),
        ]

        users = {}
        for username, email, role, user_tenant in demo_users:
            user, _ = User.objects.get_or_create(username=username)
            user.email = email
            user.role = role
            user.tenant = user_tenant
            user.is_active = True
            user.must_change_password = False
            user.temp_password_revealed = False
            user.set_password(DEMO_PASSWORD)
            user.save()
            users[username] = user

        course, _ = Course.objects.get_or_create(
            tenant=tenant,
            title="Tenant A Fundamentals",
            defaults={
                "description": "A sample course for demonstrating tenant-scoped learning.",
            },
        )
        assignment, _ = CourseAssignment.objects.get_or_create(
            course=course,
            user=users["tenant_a_user1"],
        )
        LearningProgress.objects.get_or_create(
            assignment=assignment,
            defaults={"progress_percentage": 25},
        )

        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
        self.stdout.write("Demo password: Testpassword123!")
        self.stdout.write("Demo users: superadmin, platformadmin, superviewer, tenant_a_admin, tenant_a_user1")
