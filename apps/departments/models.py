from django.db import models


class Department(models.Model):
    """
    Model Jurusan/Department di SMKN 2 Subang.
    Contoh: RPL, TPM, TSM, dll.
    """
    kode       = models.CharField(max_length=10, unique=True)
    nama       = models.CharField(max_length=100)
    bidang     = models.CharField(max_length=100)
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'departments'
        ordering = ['kode']

    def __str__(self):
        return f"{self.kode} - {self.nama}"
