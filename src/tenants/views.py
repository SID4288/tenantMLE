from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from accounts.permissions import IsSuperAdmin
from .models import Tenant
from .serializers import TenantSerializer


class TenantViewSet(ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
