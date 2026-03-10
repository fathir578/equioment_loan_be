# ============================================================
#  apps/users/models.py — Custom User Model
#
#  Kenapa custom User model?
#  Django punya User bawaan tapi tidak ada field 'role' dan
#  'qr_token'. Daripada extend nanti ribet, lebih baik ganti
#  dari awal. Ini best practice Django.
# ============================================================

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from core.utils import generate_qr_token


class UserManager(BaseUserManager):
    """
    Manager untuk User custom kita.
    Wajib ada karena kita override AbstractBaseUser.
    """

    def create_user(self, username, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email wajib diisi.')
        if not username:
            raise ValueError('Username wajib diisi.')

        email = self.normalize_email(email)
        user  = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)   # Auto hash pakai bcrypt/pbkdf2
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """Dipakai oleh: python manage.py createsuperuser"""
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Model User utama aplikasi.
    Field:
        - username, email, password (dari AbstractBaseUser)
        - role: admin | petugas | peminjam
        - qr_token: dipakai untuk QR Card identitas user
        - is_active, is_staff: dari Django auth system
    """

    class Role(models.TextChoices):
        ADMIN    = 'admin',    'Admin'
        PETUGAS  = 'petugas',  'Petugas'
        PEMINJAM = 'peminjam', 'Peminjam'

    username   = models.CharField(max_length=50, unique=True)
    email      = models.EmailField(unique=True)
    role       = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.PEMINJAM,
    )
    qr_token   = models.CharField(
        max_length=64,
        unique=True,
        editable=False,     # Tidak bisa diubah via form
        help_text='Token unik yang di-encode menjadi QR Card user.'
    )
    is_active  = models.BooleanField(default=True)
    is_staff   = models.BooleanField(default=False)  # Akses Django Admin
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Konfigurasi Django auth
    USERNAME_FIELD  = 'username'
    REQUIRED_FIELDS = ['email']
    objects         = UserManager()

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes  = [
            models.Index(fields=['role']),
            models.Index(fields=['qr_token']),
        ]

    def save(self, *args, **kwargs):
        # Auto-generate qr_token saat pertama kali dibuat
        if not self.qr_token:
            self.qr_token = generate_qr_token()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.username} ({self.role})'

    # Helper properties untuk cek role di kode
    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_petugas(self):
        return self.role == self.Role.PETUGAS

    @property
    def is_peminjam(self):
        return self.role == self.Role.PEMINJAM
