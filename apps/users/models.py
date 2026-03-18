# ============================================================
#  apps/users/models.py — Custom User Model [v2.0.0]
# ============================================================

from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from apps.departments.models import Department


class UserManager(BaseUserManager):
    """
    Manager untuk User custom kita.
    """

    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError('Username wajib diisi.')

        if email:
            email = self.normalize_email(email)
        
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        """Dipakai oleh: python manage.py createsuperuser"""
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if not email:
            raise ValueError('Superuser wajib memiliki email.')
            
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Model User utama aplikasi v2.0.0.
    """

    class Role(models.TextChoices):
        ADMIN    = 'admin',    'Admin'
        PETUGAS  = 'petugas',  'Petugas'
        PEMINJAM = 'peminjam', 'Peminjam'

    username     = models.CharField(max_length=50, unique=True)
    email        = models.EmailField(unique=True, null=True, blank=True)
    role         = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.PEMINJAM,
    )
    
    # [NEW v2.0.0] Identitas Siswa (Peminjam)
    department   = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    nis          = models.CharField(max_length=20, unique=True, null=True, blank=True)
    nama_lengkap = models.CharField(max_length=100, null=True, blank=True)
    kelas        = models.CharField(max_length=20, null=True, blank=True)
    is_verified  = models.BooleanField(default=False)

    qr_token     = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        help_text='Token unik yang di-encode menjadi QR Card user.'
    )
    is_active    = models.BooleanField(default=True)
    is_staff     = models.BooleanField(default=False)
    created_at   = models.DateTimeField(auto_now_add=True)
    updated_at   = models.DateTimeField(auto_now=True)

    USERNAME_FIELD  = 'username'
    REQUIRED_FIELDS = [] # Email tidak lagi wajib secara global di level model
    objects         = UserManager()

    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        indexes  = [
            models.Index(fields=['role']),
            models.Index(fields=['qr_token']),
            models.Index(fields=['nis']),
        ]

    def clean(self):
        super().clean()
        
        # Validasi Admin/Petugas: Wajib email domain tertentu
        if self.role in [self.Role.ADMIN, self.Role.PETUGAS]:
            if not self.email:
                raise ValidationError({'email': 'Admin dan Petugas wajib memiliki email.'})
            if not self.email.endswith('@smk-2sbg.sch.id'):
                raise ValidationError({'email': 'Email harus menggunakan domain @smk-2sbg.sch.id'})
        
        # Validasi Peminjam: Wajib identitas siswa
        if self.role == self.Role.PEMINJAM:
            errors = {}
            if not self.nis:
                errors['nis'] = 'Siswa wajib memiliki NIS.'
            if not self.nama_lengkap:
                errors['nama_lengkap'] = 'Siswa wajib memiliki nama lengkap.'
            if not self.kelas:
                errors['kelas'] = 'Siswa wajib memiliki kelas.'
            if not self.department:
                errors['department'] = 'Siswa wajib terdaftar di jurusan.'
            
            if errors:
                raise ValidationError(errors)

    def save(self, *args, **kwargs):
    # Hanya jalankan full_clean untuk role yang butuh validasi ketat
        if self.role in [self.Role.PEMINJAM]:
            self.full_clean()

        if not self.qr_token:
            from core.utils import generate_qr_token
            self.qr_token = generate_qr_token()

        super().save(*args, **kwargs)
    def __str__(self):
        if self.role == self.Role.PEMINJAM:
            return f'{self.nama_lengkap} ({self.nis})'
        return f'{self.username} ({self.role})'

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_petugas(self):
        return self.role == self.Role.PETUGAS

    @property
    def is_peminjam(self):
        return self.role == self.Role.PEMINJAM
