# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .permissions import IsSuperAdmin

class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "tenant": user.tenant_id,
        })

class SuperAdminTestView(APIView):
    permission_classes = [IsSuperAdmin]

    def get(self, request):
        return Response({
            "message": "You are allowed to access this endpoint.",
            "role": request.user.role,
        })
