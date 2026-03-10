# ============================================================
#  apps/loans/models.py
#
#  [Bug 5] Tambah validasi role approved_by di clean()
#  [Bug 6] Tambah status 'partial_returned'
#          Tambah quantity_returned di LoanItem
# ============================================================

from django.db import models
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from apps.tools.models import Tool


class Loan(models.Model):

    class Status(models.TextChoices):
        PENDING          = 'pending',          'Menunggu Persetujuan'
        APPROVED         = 'approved',         'Disetujui'
        REJECTED         = 'rejected',         'Ditolak'
        PARTIAL_RETURNED = 'partial_returned', 'Sebagian Dikembalikan'  # [Bug 6]
        RETURNED         = 'returned',         'Sudah Dikembalikan'

    # Status yang dianggap "masih aktif" (alat sedang di luar)
    ACTIVE_STATUSES = [Status.APPROVED, Status.PARTIAL_RETURNED]

    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='loans',
        limit_choices_to={'role': 'peminjam'},
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_loans',
        db_column='approved_by',
    )
    loan_date   = models.DateField()
    due_date    = models.DateField()
    status      = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
    )
    notes       = models.TextField(blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'loans'
        ordering = ['-created_at']

    def clean(self):
        errors = {}

        # Validasi tanggal
        if self.due_date and self.loan_date and self.due_date < self.loan_date:
            errors['due_date'] = 'Tanggal kembali tidak boleh sebelum tanggal pinjam.'

        # [Bug 5] Validasi role approved_by di layer Django
        # (DB trigger juga validasi sebagai safety net)
        if self.approved_by_id:
            if self.approved_by_id == self.user_id:
                errors['approved_by'] = 'Peminjam tidak boleh menyetujui loan miliknya sendiri.'

            if hasattr(self, '_approved_by_cache'):
                approver = self._approved_by_cache
            else:
                try:
                    from apps.users.models import User
                    approver = User.objects.get(pk=self.approved_by_id)
                    self._approved_by_cache = approver
                except User.DoesNotExist:
                    errors['approved_by'] = 'Approver tidak ditemukan.'
                    approver = None

            if approver and approver.role not in ('petugas', 'admin'):
                errors['approved_by'] = 'Hanya Petugas atau Admin yang bisa menyetujui peminjaman.'

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f'Loan #{self.id} — {self.user.username} ({self.status})'

    @property
    def is_overdue(self):
        from datetime import date
        return self.status in self.ACTIVE_STATUSES and self.due_date < date.today()

    @property
    def is_fully_returned(self):
        return self.status == self.Status.RETURNED

    @property
    def is_partially_returned(self):
        return self.status == self.Status.PARTIAL_RETURNED


class LoanItem(models.Model):
    """
    Detail alat dalam satu peminjaman.

    [Bug 6] quantity_returned melacak berapa unit sudah dikembalikan.
    Berguna untuk partial return.
    """
    loan              = models.ForeignKey(
        Loan, on_delete=models.CASCADE, related_name='items'
    )
    tool              = models.ForeignKey(
        Tool, on_delete=models.PROTECT, related_name='loan_items'
    )
    quantity          = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)]
    )
    quantity_returned = models.PositiveIntegerField(
        default=0,
        help_text='Berapa unit yang sudah dikembalikan. Diupdate otomatis oleh trigger.'
    )

    class Meta:
        db_table        = 'loan_items'
        unique_together = [('loan', 'tool')]

    def clean(self):
        if self.quantity_returned > self.quantity:
            raise ValidationError(
                f'quantity_returned ({self.quantity_returned}) '
                f'tidak boleh melebihi quantity ({self.quantity}).'
            )

    @property
    def remaining_quantity(self):
        """Berapa unit yang belum dikembalikan."""
        return self.quantity - self.quantity_returned

    @property
    def is_fully_returned(self):
        return self.quantity_returned >= self.quantity

    def __str__(self):
        return (
            f'{self.tool.name} x{self.quantity} '
            f'(kembali: {self.quantity_returned}) — Loan #{self.loan_id}'
        )
