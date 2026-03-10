from django.test import TestCase, TransactionTestCase
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
    Menggunakan TransactionTestCase karena kita menguji Stored Procedures.
    """

    def setUp(self):
        # 1. Setup Data Awal
        self.admin = User.objects.create_superuser(username='admin_test', email='admin@test.com', password='password')
        self.siswa = User.objects.create_user(username='siswa_test', email='siswa@test.com', password='password')
        self.cat = Category.objects.create(name='Test Cat')
        self.tool = Tool.objects.create(
            category=self.cat,
            name='Tool Test',
            stock_total=10,
            stock_available=10
        )

    def test_stock_decrease_on_approve(self):
        """Uji apakah stok berkurang otomatis saat loan disetujui."""
        # Buat loan via SP
        with connection.cursor() as cursor:
            cursor.execute("SET @p_loan_id = 0")
            cursor.execute("SET @p_message = ''")
            items = [{'tool_id': self.tool.id, 'qty': 3}]
            cursor.execute(
                "CALL sp_create_loan(%s, %s, %s, %s, %s, @p_loan_id, @p_message)",
                [self.siswa.id, date.today(), date.today() + timedelta(days=5), 'Test', json.dumps(items)]
            )
            cursor.execute("SELECT @p_loan_id")
            loan_id = cursor.fetchone()[0]

        loan = Loan.objects.get(id=loan_id)
        
        # Approve loan
        loan.status = 'approved'
        loan.approved_by = self.admin
        loan.save()

        # Cek stok alat
        self.tool.refresh_from_db()
        self.assertEqual(self.tool.stock_available, 7)

    def test_fine_calculation(self):
        """Uji apakah denda terhitung otomatis saat telat."""
        # 1. Buat Loan yang sudah expired
        loan = Loan.objects.create(
            user=self.siswa,
            loan_date=date.today() - timedelta(days=10),
            due_date=date.today() - timedelta(days=5),
            status='approved',
            approved_by=self.admin
        )
        li = LoanItem.objects.create(loan=loan, tool=self.tool, quantity=1)

        # 2. Proses return via SP
        with connection.cursor() as cursor:
            cursor.execute("SET @p_return_id = 0")
            cursor.execute("SET @p_late_days = 0")
            cursor.execute("SET @p_total_fine = 0.00")
            cursor.execute("SET @p_message = ''")
            items = [{'loan_item_id': li.id, 'qty_returned': 1, 'condition': 'baik'}]
            cursor.execute(
                "CALL sp_process_return(%s, %s, %s, %s, %s, %s, @p_return_id, @p_late_days, @p_total_fine, @p_message)",
                [loan.id, self.admin.id, date.today(), 5000, json.dumps(items), 'Return telat']
            )
            cursor.execute("SELECT @p_total_fine")
            total_fine = cursor.fetchone()[0]

        # Telat 5 hari * 5000 = 25000
        self.assertEqual(float(total_fine), 25000.00)
