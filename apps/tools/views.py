from rest_framework import viewsets, permissions
from apps.tools.models import Tool
from apps.tools.serializers import ToolSerializer
from core.permissions import IsAdminOrPetugas

class ToolViewSet(viewsets.ModelViewSet):
    queryset = Tool.objects.all()
    serializer_class = ToolSerializer
    filterset_fields = ['category', 'condition', 'is_active']
    search_fields = ['name', 'description', 'qr_code']

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrPetugas()]
        return [permissions.IsAuthenticated()]
