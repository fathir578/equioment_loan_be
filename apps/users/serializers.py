import secrets
import re
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from apps.departments.models import Department
from core.utils import generate_qr_user

User = get_user_model()

ALLOWED_DOMAINS = [
    'smk-2sbg.sch.id',
]

class UserSerializer(serializers.ModelSerializer):
    department_kode = serializers.CharField(source='department.kode', read_only=True)
    
    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'role', 'qr_token', 
            'nis', 'nama_lengkap', 'kelas', 'department', 'department_kode',
            'is_verified', 'is_active', 'created_at'
        )
        read_only_fields = ('qr_token', 'is_verified', 'created_at')

class RegisterSerializer(serializers.ModelSerializer):
    """Serializer untuk registrasi Admin/Petugas (pakai email)"""
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'role')

    def validate_email(self, value):
        domain = value.split('@')[-1]
        if domain not in ALLOWED_DOMAINS:
            raise serializers.ValidationError(
                f'Email harus menggunakan domain {", ".join(ALLOWED_DOMAINS)}'
            )
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

# ------------------------------------------------------------
# [NEW v2.0.0] PEMINJAM (SISWA) SERIALIZERS
# ------------------------------------------------------------

def validate_kelas(value):
    """
    Format: "X RPL", "XI TPM", "XII KUL"
    Atau dengan huruf kelas: "X RPL A", "XI TPM B"
    Huruf kelas opsional.
    Auto uppercase.
    """
    val = value.upper().strip()
    
    # Dengan huruf kelas: "XI RPL A" atau tanpa: "XI RPL"
    pattern = r'^(X|XI|XII)\s[A-Z]+(\s[A-Z])?$'
    
    if not re.match(pattern, val):
        raise serializers.ValidationError(
            'Format kelas salah. Contoh: "X RPL" atau "X RPL A"'
        )
    return val

class PeminjamCreateSerializer(serializers.ModelSerializer):
    """
    Serializer khusus pendaftaran siswa oleh Admin/Petugas.
    Username auto-set ke NIS.
    Password auto-generate.
    """
    kelas = serializers.CharField(validators=[validate_kelas])
    
    class Meta:
        model = User
        fields = ('nis', 'nama_lengkap', 'kelas', 'department')

    def create(self, validated_data):
        nis = validated_data['nis']
        # Password auto-generate
        password = secrets.token_urlsafe(12)
        
        user = User.objects.create_user(
            username=nis, # Username pake NIS biar gampang login
            password=password,
            role=User.Role.PEMINJAM,
            is_verified=False, # Default belum verified
            **validated_data
        )
        
        # Generate fisik gambar QR
        generate_qr_user(user)
        
        # Tambahkan password plain ke instance (hanya untuk response sekali ini)
        user.plain_password = password
        return user

    def to_representation(self, instance):
        repr = super().to_representation(instance)
        # Tampilkan password sekali saja saat create
        if hasattr(instance, 'plain_password'):
            repr['password_temp'] = instance.plain_password
        return repr

class PeminjamVerifySerializer(serializers.ModelSerializer):
    """Untuk petugas memverifikasi siswa"""
    class Meta:
        model = User
        fields = ('is_verified',)

    def update(self, instance, validated_data):
        instance.is_verified = validated_data.get('is_verified', instance.is_verified)
        instance.save()
        return instance

# ------------------------------------------------------------
# AUTH SERIALIZERS
# ------------------------------------------------------------

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['role'] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data
