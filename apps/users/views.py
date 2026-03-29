from rest_framework import generics, status, viewsets, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django_filters.rest_framework import DjangoFilterBackend
from django.db import models
from apps.users.serializers import (
    UserSerializer, RegisterSerializer, MyTokenObtainPairSerializer,
    PeminjamCreateSerializer, PeminjamVerifySerializer, PetugasCreateSerializer,
    PetugasUpdateSerializer
)
from core.utils import success_response, created_response
from core.permissions import IsAdmin, CanRegisterPeminjam, IsSameDepartment

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    """Untuk registrasi admin/petugas awal atau via AllowAny jika diizinkan"""
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        data = UserSerializer(user).data
        return created_response(data, message="Registrasi berhasil.")

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            token = RefreshToken(refresh_token)
            token.blacklist()
            return success_response(message="Logout berhasil.")
        except Exception:
            return Response({"success": False, "message": "Token tidak valid."}, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        serializer = UserSerializer(request.user)
        return success_response(serializer.data)

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet untuk manajemen user.
    v2.0.0: Ditambah fitur registrasi & verifikasi siswa.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsSameDepartment]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['role', 'is_active', 'department', 'is_verified']
    search_fields = ['username', 'email', 'nis', 'nama_lengkap']

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return User.objects.all()
        elif user.role == 'petugas':
            # Petugas hanya bisa lihat user di jurusannya (terutama siswa)
            return User.objects.filter(department=user.department)
        # Peminjam cuma bisa lihat diri sendiri
        return User.objects.filter(id=user.id)

    # ------------------------------------------------------------
    # [NEW v2.0.0] SISWA (PEMINJAM) ENDPOINTS
    # ------------------------------------------------------------

    @action(detail=False, methods=['get', 'post'], permission_classes=[permissions.IsAuthenticated])
    def peminjam(self, request):
        """
        [v2.0.0] Endpoint Peminjam (Siswa)
        POST -> Daftar siswa (Hanya CanRegisterPeminjam)
        GET  -> List siswa (Semua terautentikasi)
        """
        if request.method == 'POST':
            # Cek permission manual untuk POST
            if not CanRegisterPeminjam().has_permission(request, self):
                return Response(
                    {"success": False, "message": "Hanya Admin/Petugas yang bisa mendaftar."},
                    status=status.HTTP_403_FORBIDDEN
                )
                
            serializer = PeminjamCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            
            if request.user.role == 'petugas' and not user.department:
                user.department = request.user.department
                user.save()

            data = PeminjamCreateSerializer(user).data
            return created_response(data, message="Siswa berhasil didaftarkan.")

        # GET Logic
        queryset = self.get_queryset().filter(role=User.Role.PEMINJAM)
        
        dept = request.query_params.get('dept')
        if dept:
            queryset = queryset.filter(department__kode=dept)
            
        kelas = request.query_params.get('kelas')
        if kelas:
            queryset = queryset.filter(kelas__iexact=kelas)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[CanRegisterPeminjam])
    def verify(self, request, pk=None):
        """POST /api/v1/users/{id}/verify/ -> Verifikasi siswa"""
        user_to_verify = self.get_object()
        if user_to_verify.role != User.Role.PEMINJAM:
            return Response(
                {"success": False, "message": "Hanya akun siswa yang bisa diverifikasi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PeminjamVerifySerializer(user_to_verify, data={'is_verified': True}, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return success_response(message=f"Siswa {user_to_verify.nama_lengkap} berhasil diverifikasi.")

    @action(detail=False, methods=['get'], permission_classes=[CanRegisterPeminjam])
    def pending(self, request):
        """GET /api/v1/users/pending/ -> List siswa belum diverifikasi"""
        queryset = self.get_queryset().filter(role=User.Role.PEMINJAM, is_verified=False)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(serializer.data)

    # ------------------------------------------------------------
    # [NEW] PETUGAS ENDPOINTS
    # ------------------------------------------------------------

    @action(detail=False, methods=['get', 'post'], permission_classes=[permissions.IsAuthenticated, IsAdmin])
    def petugas(self, request):
        """
        GET /api/v1/users/petugas/ -> List all petugas users
        POST /api/v1/users/petugas/ -> Create new petugas user

        GET Query params:
        - search: filter by username or nama_lengkap (case insensitive)
        - department: filter by department_id
        - page_size: number of results per page

        POST Required fields:
        - username (string)
        - email (string, must be @smk-2sbg.sch.id)
        - nama_lengkap (string)
        - department (integer, department ID)
        - password (string, min 6 characters)

        Only accessible by admin users.
        """
        if request.method == 'POST':
            serializer = PetugasCreateSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()

            data = UserSerializer(user).data
            return created_response(data, message="Petugas berhasil dibuat.")

        # GET Logic
        queryset = User.objects.filter(role=User.Role.PETUGAS)

        # Filter by search (username or nama_lengkap)
        search = request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                models.Q(username__icontains=search) |
                models.Q(nama_lengkap__icontains=search)
            )

        # Filter by department
        department = request.query_params.get('department', None)
        if department:
            queryset = queryset.filter(department_id=department)

        # Pagination with page_size param (custom pagination)
        page_size = request.query_params.get('page_size', None)
        if page_size:
            try:
                page_size = int(page_size)
                from django.core.paginator import Paginator
                paginator = Paginator(queryset, page_size)
                page_number = request.query_params.get('page', 1)
                page_obj = paginator.get_page(page_number)

                data = UserSerializer(page_obj.object_list, many=True).data
                return success_response({
                    'count': paginator.count,
                    'results': data,
                    'page': page_obj.number,
                    'pages': paginator.num_pages
                })
            except (ValueError, TypeError):
                pass

        # Default: return all results with count
        serializer = self.get_serializer(queryset, many=True)
        return success_response({
            'count': queryset.count(),
            'results': serializer.data
        })

    def update_petugas(self, request, pk=None):
        """
        PUT /api/v1/users/petugas/{id}/ -> Update petugas user

        Optional fields:
        - username (string)
        - email (string, must be @smk-2sbg.sch.id)
        - nama_lengkap (string)
        - department (integer, department ID)
        - password (string, min 6 characters, optional)

        Only accessible by admin users.
        """
        user_to_modify = self.get_object()
        
        # Ensure user is a petugas
        if user_to_modify.role != User.Role.PETUGAS:
            return Response(
                {"success": False, "message": "User bukan petugas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = PetugasUpdateSerializer(user_to_modify, data=request.data, partial=False)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        data = UserSerializer(user_to_modify).data
        return success_response(data, message="Petugas berhasil diupdate.")

    def delete_petugas(self, request, pk=None):
        """
        DELETE /api/v1/users/petugas/{id}/ -> Delete petugas user

        Only accessible by admin users.
        
        Note: Cannot delete if petugas has related Return records.
        """
        from django.db.models.deletion import ProtectedError
        
        user_to_modify = self.get_object()
        
        # Ensure user is a petugas
        if user_to_modify.role != User.Role.PETUGAS:
            return Response(
                {"success": False, "message": "User bukan petugas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user_to_modify.delete()
            return success_response(message="Petugas berhasil dihapus.")
        except ProtectedError:
            return Response(
                {
                    "success": False,
                    "message": "Petugas tidak dapat dihapus karena masih memiliki data terkait (riwayat pengembalian)."
                },
                status=status.HTTP_409_CONFLICT
            )

    def retrieve_petugas(self, request, pk=None):
        """
        GET /api/v1/users/petugas/{id}/ -> Get single petugas user

        Only accessible by admin users.
        """
        user_to_retrieve = self.get_object()
        
        # Ensure user is a petugas
        if user_to_retrieve.role != User.Role.PETUGAS:
            return Response(
                {"success": False, "message": "User bukan petugas."},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = UserSerializer(user_to_retrieve).data
        return success_response(data)
