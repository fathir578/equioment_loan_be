# ============================================================
#  apps/returns/models.py
#
#  [Bug 4] condition_on_return dipindah ke ReturnItem (per alat)
#  [Bug 6] Satu loan bisa punya banyak Return (partial return)
#          Tambah model ReturnItem
# ============================================================

from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from apps.loans.models import Loan, LoanItem


class Return(models.Model):
    """
    Satu sesi pengembalian.

    [Bug 6] Tidak lagi OneToOne dengan Loan —
    satu loan bisa punya BANYAK sesi pengembalian (partial return).
    Detail alat yang dikembalikan ada di ReturnItem.
    """
    loan         = models.ForeignKey(
        Loan,
        on_delete=models.PROTECT,
        related_name='return_records',  # bukan 'return_record' karena bisa banyak
    )
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='processed_returns',
        db_column='processed_by',
    )
    return_date  = models.DateField()
    late_days    = models.PositiveIntegerField(default=0)
    fine_per_day = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_fine   = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes        = models.TextField(blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'returns'
        ordering = ['-created_at']

    def __str__(self):
        return f'Return #{self.id} for Loan #{self.loan_id} | Denda: Rp{self.total_fine:,.0f}'

    @property
    def is_late(self):
        return self.late_days > 0


class ReturnItem(models.Model):
    """
    Detail per-alat dalam satu sesi pengembalian.

    [Bug 4] condition_on_return ada di sini karena kondisi
    bersifat per-alat. Trigger DB yang akan membaca ini dan
    mengupdate tools.condition (hanya downgrade).

    [Bug 6] Partial return — quantity_returned bisa kurang
    dari quantity yang dipinjam.
    """

    class Condition(models.TextChoices):
        BAIK         = 'baik',         'Baik'
        RUSAK_RINGAN = 'rusak_ringan', 'Rusak Ringan'
        RUSAK_BERAT  = 'rusak_berat',  'Rusak Berat'

    # Mapping kondisi ke angka untuk perbandingan downgrade
    CONDITION_SEVERITY = {
        'baik': 0,
        'rusak_ringan': 1,
        'rusak_berat': 2,
    }

    return_record       = models.ForeignKey(
        Return,
        on_delete=models.CASCADE,
        related_name='items',
        db_column='return_id',
    )
    loan_item           = models.ForeignKey(
        LoanItem,
        on_delete=models.PROTECT,
        related_name='return_items',
        db_column='loan_item_id',
    )
    quantity_returned   = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )
    condition_on_return = models.CharField(
        max_length=15,
        choices=Condition.choices,
        default=Condition.BAIK,
        help_text='Kondisi alat saat dikembalikan. Trigger DB akan update tools.condition jika lebih buruk.'
    )

    class Meta:
        db_table        = 'return_items'
        unique_together = [('return_record', 'loan_item')]

    def clean(self):
        # Validasi quantity_returned tidak melebihi sisa yang belum kembali
        if self.loan_item_id and self.quantity_returned:
            remaining = self.loan_item.remaining_quantity
            if self.quantity_returned > remaining:
                raise ValidationError(
                    f'Jumlah yang dikembalikan ({self.quantity_returned}) '
                    f'melebihi sisa yang belum kembali ({remaining}).'
                )

    def __str__(self):
        return (
            f'ReturnItem #{self.id} — '
            f'{self.loan_item.tool.name} x{self.quantity_returned} '
            f'({self.condition_on_return})'
        )
