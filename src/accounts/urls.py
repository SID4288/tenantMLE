from django.urls import path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import MeView, SuperAdminTestView
from rest_framework.routers import DefaultRouter
from .views import (
    ApplicationStatusView,
    ChangePasswordView,
    MeView,
    SuperAdminTestView,
    TenantApplicationView,
    TenantUserRegistrationView,
    UserViewSet,
)
router = DefaultRouter()
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", MeView.as_view(), name="me"),
    path("register/", TenantUserRegistrationView.as_view(), name="register"),
    path(
        "tenant-application/",
        TenantApplicationView.as_view(),
        name="tenant_application",
    ),
    path(
        "application-status/",
        ApplicationStatusView.as_view(),
        name="application_status",
    ),
    path(
        "change-password/",
        ChangePasswordView.as_view(),
        name="change_password",
    ),
    path("super-admin-test/", SuperAdminTestView.as_view(), name="super_admin_test"),
] + router.urls
