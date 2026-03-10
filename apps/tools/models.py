# ============================================================
#  apps/tools/models.py — Model Alat
# ============================================================

from django.db import models
from django.core.validators import MinValueValidator
from apps.categories.models import Category
from core.utils import generate_qr_token


class Tool(models.Model):

    class Condition(models.TextChoices):
        BAIK         = 'baik',         'Baik'
        RUSAK_RINGAN = 'rusak_ringan', 'Rusak Ringan'
        RUSAK_BERAT  = 'rusak_berat',  'Rusak Berat'

    category        = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,   # Tidak bisa hapus kategori yang masih punya alat
        related_name='tools'
    )
    name            = models.CharField(max_length=150)
    description     = models.TextField(blank=True)
    qr_code         = models.CharField(
        max_length=64,
        unique=True,
        editable=False,
        help_text='Token unik yang di-encode menjadi QR label alat.'
    )
    stock_total     = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    stock_available = models.PositiveIntegerField(default=1)
    condition       = models.CharField(
        max_length=15,
        choices=Condition.choices,
        default=Condition.BAIK
    )
    is_active       = models.BooleanField(default=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'tools'
        ordering = ['name']
        indexes  = [
            models.Index(fields=['qr_code']),
            models.Index(fields=['category']),
            models.Index(fields=['is_active']),
        ]

    def save(self, *args, **kwargs):
        # Auto-generate qr_code saat alat pertama kali dibuat
        if not self.qr_code:
            from core.utils import generate_qr_token, generate_qr_image
            self.qr_code = generate_qr_token()
            # Generate fisik gambar QR
            generate_qr_image(self.qr_code, f'tool_{self.qr_code[:8]}')

        # Pastikan stock_available tidak melebihi stock_total
        if self.stock_available > self.stock_total:
            self.stock_available = self.stock_total
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.name} (stok: {self.stock_available}/{self.stock_total})'

    @property
    def is_available(self):
        return self.is_active and self.stock_available > 0
