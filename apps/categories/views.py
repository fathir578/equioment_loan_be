from rest_framework import viewsets, permissions
from apps.categories.models import Category
from apps.categories.serializers import CategorySerializer
from core.permissions import IsAdminOrPetugas

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrPetugas()]
        return [permissions.IsAuthenticated()]
