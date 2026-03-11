# ============================================================
#  apps/activity_logs/models.py — Audit Trail
# ============================================================

from django.db import models
from django.conf import settings


class ActivityLog(models.Model):
    """
    Mencatat semua aksi penting di sistem.
    SET_NULL pada user: kalau user dihapus, log tetap ada
    tapi user_id menjadi NULL. Ini intentional — log
    tidak boleh ikut terhapus (audit trail harus utuh).
    """
    user        = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='activity_logs',
    )
    action      = models.CharField(max_length=100)       # Contoh: "POST /api/v1/loans/"
    description = models.TextField(blank=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    user_agent  = models.TextField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'activity_logs'
        ordering = ['-created_at']
        indexes  = [
            models.Index(fields=['user']),
            models.Index(fields=['action']),
            models.Index(fields=['created_at']),
            models.Index(fields=['ip_address']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else 'System'
        return f'[{self.created_at:%Y-%m-%d %H:%M}] {user_str} — {self.action}'
