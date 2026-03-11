from django.test import TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import connection
from apps.categories.models import Category
from apps.tools.models import Tool
from apps.loans.models import Loan, LoanItem
from datetime import date, timedelta
import json

User = get_user_model()

class BusinessLogicTest(TransactionTestCase):
    """
    Test case untuk menguji logika bisnis utama di level Database (Trigger & SP).
    
    CATATAN PENTING:
    Karena sistem menggunakan Stored Procedures & Triggers manual yang 
    mengandung 'DELIMITER $$', disarankan menjalankan test ini pada 
    environment yang sudah memiliki skema DB lengkap.
    """

    def setUp(self):
        # Gunakan get_or_create untuk menghindari duplikasi jika database test tidak di-reset bersih
        self.admin, _ = User.objects.get_or_create(
            username='admin_test', 
            defaults={'email': 'admin@test.com', 'role': 'admin', 'is_staff': True}
        )
        self.admin.set_password('password')
        self.admin.save()

        self.siswa, _ = User.objects.get_or_create(
            username='siswa_test', 
            defaults={'email': 'siswa@test.com', 'role': 'peminjam'}
        )
        
        self.cat, _ = Category.objects.get_or_create(name='Test Cat')
        
        self.tool, _ = Tool.objects.get_or_create(
            name='Tool Test',
            defaults={
                'category': self.cat,
                'stock_total': 10,
                'stock_available': 10,
                'qr_code': 'test_qr_123'
            }
        )

    def test_stock_decrease_on_approve(self):
        """Uji apakah stok berkurang otomatis saat loan disetujui via Trigger."""
        # Buat loan
        loan = Loan.objects.create(
            user=self.siswa,
            loan_date=date.today(),
            due_date=date.today() + timedelta(days=5),
            status='pending'
        )
        LoanItem.objects.create(loan=loan, tool=self.tool, quantity=3)

        # Trigger trg_update_stock_on_approve jalan saat status jadi 'approved'
        loan.status = 'approved'
        loan.approved_by = self.admin
        loan.save()

        # Cek stok alat
        self.tool.refresh_from_db()
        # Jika trigger aktif, stok harus jadi 10 - 3 = 7
        # Note: Jika dijalankan di database kosong tanpa trigger, ini akan tetap 10 (dan test akan fail sebagai peringatan)
        self.assertEqual(self.tool.stock_available, 7, "Trigger database untuk pengurangan stok tidak berjalan.")

    def test_fine_calculation_logic(self):
        """Uji logika denda sederhana."""
        from core.utils import calculate_fine
        
        due = date.today() - timedelta(days=5)
        now = date.today()
        
        res = calculate_fine(due, now, 5000)
        # Telat 5 hari * 5000 = 25000
        self.assertEqual(res['total_fine'], 25000.00)
