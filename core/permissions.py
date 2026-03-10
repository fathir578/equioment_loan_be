# ============================================================
#  core/permissions.py — RBAC: izin per role
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

    Dipakai di endpoint seperti GET /loans/{id}
    → Peminjam hanya bisa lihat loan miliknya sendiri.
    """
    message = 'Akses ditolak. Anda hanya bisa mengakses data milik sendiri.'

    def has_object_permission(self, request, view, obj):
        if request.user.role == 'admin':
            return True
        # Cek apakah object punya field user/user_id
        owner = getattr(obj, 'user', None) or getattr(obj, 'user_id', None)
        return owner == request.user or owner == request.user.id
