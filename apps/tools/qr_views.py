from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, serializers
from django.db import connection
from core.permissions import IsAdminOrPetugas
from drf_spectacular.utils import extend_schema, OpenApiExample


class QRScanInputSerializer(serializers.Serializer):
    qr_value = serializers.CharField(help_text="Token QR code user atau alat")
    type     = serializers.ChoiceField(
        choices=['user', 'tool'],
        help_text="Tipe scan: 'user' untuk siswa, 'tool' untuk alat"
    )


@extend_schema(
    request=QRScanInputSerializer,
    examples=[
        OpenApiExample(
            'Scan Siswa',
            value={'qr_value': 'abc123...', 'type': 'user'}
        ),
        OpenApiExample(
            'Scan Alat',
            value={'qr_value': 'xyz789...', 'type': 'tool'}
        ),
    ]
)
class QRScanView(APIView):
    """
    POST /api/v1/qr-scan/
    Scan QR code untuk identifikasi siswa atau alat.
    Hanya Admin dan Petugas yang bisa scan.
    """
    permission_classes = [IsAdminOrPetugas]

    def post(self, request):
        serializer = QRScanInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({
                'success': False,
                'message': 'Input tidak valid.',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        qr_value  = serializer.validated_data['qr_value']
        scan_type = serializer.validated_data['type']

        if scan_type == 'user':
            return self._scan_user(qr_value)
        return self._scan_tool(qr_value)

    def _scan_user(self, qr_value):
        with connection.cursor() as cursor:
        # Sesuai parameter SP yang ada: 5 parameter
            cursor.execute("SET @p_found=0, @p_user_id=0, @p_username='', @p_role=''")
            cursor.execute("""
            CALL sp_get_user_by_qr(%s, @p_found, @p_user_id, @p_username, @p_role)
        """, [qr_value])
            cursor.execute("SELECT @p_found, @p_user_id, @p_username, @p_role")
            row = cursor.fetchone()

    # p_found = 0 artinya tidak ditemukan
        if not row or row[0] == 0:
            return Response({
                'success': False,
                'message': 'QR tidak valid atau siswa tidak aktif.'
            }, status=status.HTTP_404_NOT_FOUND)

    # Ambil data lengkap via Django ORM
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            user = User.objects.select_related('department').get(id=row[1])
        except User.DoesNotExist:
            return Response({
                'success': False,
                'message': 'User tidak ditemukan.'
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'success': True,
            'message': 'Siswa ditemukan.',
            'data': {
            'user_id':      user.id,
            'nama_lengkap': user.nama_lengkap or user.username,
            'nis':          user.nis,
            'kelas':        user.kelas,
            'jurusan':      user.department.kode if user.department else None,
            'role':         user.role,
        }
    })

    def _scan_tool(self, qr_value):
        with connection.cursor() as cursor:
            cursor.execute("SET @p_tool_id=0, @p_name='', @p_stock=0")
            cursor.execute("""
                CALL sp_get_tool_by_qr(%s, @p_tool_id, @p_name, @p_stock)
            """, [qr_value])
            cursor.execute("SELECT @p_tool_id, @p_name, @p_stock")
            row = cursor.fetchone()

        if not row or row[0] == 0:
            return Response({
                'success': False,
                'message': 'QR alat tidak valid atau alat tidak tersedia.'
            }, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'success': True,
            'message': 'Alat ditemukan.',
            'data': {
                'tool_id':         row[0],
                'name':            row[1],
                'stock_available': row[2],
            }
        })
