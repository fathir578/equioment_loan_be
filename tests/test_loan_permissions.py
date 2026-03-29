from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.departments.models import Department
from apps.loans.models import Loan
from datetime import date

User = get_user_model()


class LoanPermissionTest(TestCase):
    """Test permission untuk endpoint loan detail"""

    def setUp(self):
        self.client = APIClient()
        
        # Create department
        self.department, _ = Department.objects.get_or_create(
            kode='RPL',
            defaults={'nama': 'Rekayasa Perangkat Lunak'}
        )

        # Create admin user
        self.admin = User.objects.create_user(
            username='admin_test',
            email='admin@smk-2sbg.sch.id',
            password='adminpass123',
            role=User.Role.ADMIN,
            is_staff=True
        )

        # Create petugas user
        self.petugas = User.objects.create_user(
            username='petugas_test',
            email='petugas@smk-2sbg.sch.id',
            password='petugaspass123',
            role=User.Role.PETUGAS,
            is_staff=True,
            is_verified=True,
            department=self.department
        )

        # Create siswa/peminjam user
        self.siswa = User.objects.create_user(
            username='123456',
            email='siswa@smk-2sbg.sch.id',
            password='siswapass123',
            role=User.Role.PEMINJAM,
            nis='123456',
            nama_lengkap='Siswa Test',
            kelas='X RPL',
            department=self.department
        )

        # Create another siswa (different user)
        self.siswa_lain = User.objects.create_user(
            username='654321',
            email='siswa2@smk-2sbg.sch.id',
            password='siswapass123',
            role=User.Role.PEMINJAM,
            nis='654321',
            nama_lengkap='Siswa Lain',
            kelas='XI RPL',
            department=self.department
        )

        # Create a loan for siswa
        self.loan_siswa = Loan.objects.create(
            user=self.siswa,
            loan_date=date.today(),
            due_date=date.today(),
            status='pending'
        )

    def test_admin_can_view_any_loan(self):
        """Admin bisa lihat semua peminjaman"""
        self.client.force_authenticate(user=self.admin)
        
        url = reverse('loan-detail', kwargs={'pk': self.loan_siswa.id})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_petugas_can_view_any_loan(self):
        """Petugas bisa lihat semua peminjaman (untuk approve/return)"""
        self.client.force_authenticate(user=self.petugas)
        
        url = reverse('loan-detail', kwargs={'pk': self.loan_siswa.id})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_siswa_can_view_own_loan(self):
        """Siswa bisa lihat peminjaman sendiri"""
        self.client.force_authenticate(user=self.siswa)
        
        url = reverse('loan-detail', kwargs={'pk': self.loan_siswa.id})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_siswa_cannot_view_other_loan(self):
        """Siswa TIDAK bisa lihat peminjaman siswa lain (dapat 404 karena queryset filter)"""
        # Create loan for another siswa
        loan_lain = Loan.objects.create(
            user=self.siswa_lain,
            loan_date=date.today(),
            due_date=date.today(),
            status='pending'
        )

        self.client.force_authenticate(user=self.siswa)
        
        url = reverse('loan-detail', kwargs={'pk': loan_lain.id})
        response = self.client.get(url, format='json')

        # Siswa tidak bisa akses loan siswa lain
        # Dapat 404 karena get_queryset() sudah filter
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_unauthorized_cannot_view_loan(self):
        """User tanpa auth tidak bisa lihat peminjaman"""
        url = reverse('loan-detail', kwargs={'pk': self.loan_siswa.id})
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_petugas_can_list_all_loans(self):
        """Petugas bisa list semua peminjaman"""
        self.client.force_authenticate(user=self.petugas)
        
        url = reverse('loan-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(response.data['count'], 1)

    def test_siswa_can_list_own_loans_only(self):
        """Siswa hanya bisa list peminjaman sendiri"""
        self.client.force_authenticate(user=self.siswa)
        
        url = reverse('loan-list')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should only see their own loans
        for loan in response.data['results']:
            self.assertEqual(loan['user'], self.siswa.id)
