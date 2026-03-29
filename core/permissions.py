# ============================================================
#  core/permissions.py — RBAC: izin per role [v2.0.0]
# ============================================================

from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Hanya role 'admin' yang bisa akses."""
    message = 'Akses ditolak. Hanya Admin yang diizinkan.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'admin'
        )


class IsPetugas(BasePermission):
    """Hanya role 'petugas' yang bisa akses."""
    message = 'Akses ditolak. Hanya Petugas yang diizinkan.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'petugas'
        )


class IsPeminjam(BasePermission):
    """Hanya role 'peminjam' yang bisa akses."""
    message = 'Akses ditolak. Hanya Peminjam yang diizinkan.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == 'peminjam'
        )


class IsAdminOrPetugas(BasePermission):
    """Admin atau Petugas bisa akses."""
    message = 'Akses ditolak. Hanya Admin atau Petugas yang diizinkan.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ('admin', 'petugas')
        )


class IsOwnerOrAdmin(BasePermission):
    """
    User hanya bisa akses data milik sendiri.
    Admin bisa akses data semua user.
    Petugas bisa akses data semua user (untuk proses approve/return).
    """
    message = 'Akses ditolak. Anda hanya bisa mengakses data milik sendiri.'

    def has_object_permission(self, request, view, obj):
        # Admin dan Petugas bisa akses semua data
        if request.user.role in ('admin', 'petugas'):
            return True
        
        # Peminjam hanya bisa akses data milik sendiri
        # Cek apakah object punya field user/user_id
        owner = getattr(obj, 'user', None) or getattr(obj, 'user_id', None)
        return owner == request.user or owner == request.user.id


# ------------------------------------------------------------
# [NEW v2.0.0] ADDITIONAL PERMISSIONS
# ------------------------------------------------------------

class CanRegisterPeminjam(BasePermission):
    """Hanya admin dan petugas yang bisa mendaftarkan peminjam (siswa)."""
    message = 'Akses ditolak. Hanya Admin atau Petugas yang bisa mendaftarkan siswa.'

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role in ('admin', 'petugas')
        )


class IsSameDepartment(BasePermission):
    message = 'Akses ditolak.'

    def has_permission(self, request, view):
        # Semua yang authenticated boleh akses
        # Filter dilakukan di get_queryset() di views
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False
            
        if user.role == 'admin':
            return True

        # Logika untuk Petugas
        if user.role == 'petugas':
            # Jika objek memiliki department_id atau department
            obj_dept = getattr(obj, 'department', None) or getattr(obj, 'department_id', None)
            
            # Khusus untuk model User, jika objeknya adalah user itu sendiri
            from apps.users.models import User
            if isinstance(obj, User):
                return obj.department == user.department
            
            # Khusus untuk model Loan, cek department dari peminjamnya
            from apps.loans.models import Loan
            if isinstance(obj, Loan):
                return obj.user.department == user.department

            return obj_dept == user.department

        # Logika untuk Peminjam
        if user.role == 'peminjam':
            # Jika objek adalah dirinya sendiri
            from apps.users.models import User
            if isinstance(obj, User):
                return obj == user
            
            # Jika objek adalah pinjamannya
            from apps.loans.models import Loan
            if isinstance(obj, Loan):
                return obj.user == user

        return False
