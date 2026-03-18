from rest_framework import viewsets, permissions
from apps.departments.models import Department
from apps.departments.serializers import DepartmentSerializer


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Endpoint untuk melihat daftar jurusan.
    Read-only (list & retrieve).
    Semua user terautentikasi bisa melihat.
    """
    queryset         = Department.objects.filter(is_active=True)
    serializer_class = DepartmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    search_fields    = ['kode', 'nama', 'bidang']
