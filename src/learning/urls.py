from rest_framework.routers import DefaultRouter
from .views import (
    CourseAssignmentViewSet,
    LearningProgressViewSet,
)

router = DefaultRouter()

router.register(
    "assignments",
    CourseAssignmentViewSet,
    basename="assignment",
)

router.register(
    "progress",
    LearningProgressViewSet,
    basename="progress",
)

urlpatterns = router.urls