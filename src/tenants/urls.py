from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PublicTenantListView, TenantViewSet


router = DefaultRouter()
router.register("tenants", TenantViewSet, basename="tenant")

urlpatterns = [
    # Listed before the router so "public" is not captured as a detail pk.
    path("tenants/public/", PublicTenantListView.as_view(), name="tenant-public-list"),
] + router.urls
