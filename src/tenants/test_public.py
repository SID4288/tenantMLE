from datetime import timedelta

from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

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


class PublicTenantListTests(APITestCase):
    def setUp(self):
        self.active = make_tenant(
            "Active Org", "active-org", TenantStatus.ACTIVE
        )
        self.trial = make_tenant(
            "Trial Org", "trial-org", TenantStatus.TRIAL_ACTIVE
        )
        make_tenant("Pending Org", "pending-org", TenantStatus.PENDING)
        make_tenant("Expired Org", "expired-org", TenantStatus.EXPIRED)
        self.url = reverse("tenant-public-list")

    def test_anonymous_can_list_joinable_tenants(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        slugs = {t["slug"] for t in response.data}
        self.assertEqual(slugs, {"active-org", "trial-org"})

        # Minimal fields only — no lifecycle internals leak.
        for tenant in response.data:
            self.assertEqual(
                set(tenant.keys()), {"id", "name", "slug"}
            )

    def test_joinable_tenant_ids_match_registration(self):
        listed_ids = {t["id"] for t in self.client.get(self.url).data}
        self.assertIn(self.active.id, listed_ids)
        self.assertIn(self.trial.id, listed_ids)
