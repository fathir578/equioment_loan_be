from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.departments.models import Department

User = get_user_model()


class PetugasEndpointTest(TestCase):
    """Test endpoint POST /api/v1/users/petugas/"""

    def setUp(self):
        self.client = APIClient()
        
        # Create department for testing
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

        # Create non-admin user (peminjam)
        self.peminjam = User.objects.create_user(
            username='12345',
            email='peminjam@smk-2sbg.sch.id',
            password='peminjampass123',
            role=User.Role.PEMINJAM,
            nis='12345',
            nama_lengkap='Siswa Test',
            kelas='X RPL',
            department=self.department
        )

    def _get_auth_token(self, user):
        """Helper to get JWT token"""
        url = reverse('token_obtain_pair')
        response = self.client.post(url, {
            'username': user.username,
            'password': 'adminpass123' if user == self.admin else 'peminjampass123'
        })
        return response.data.get('access')

    def test_create_petugas_success(self):
        """Admin berhasil membuat petugas baru"""
        self.client.force_authenticate(user=self.admin)
        
        data = {
            'username': 'petugas_rpl',
            'email': 'petugas@smk-2sbg.sch.id',
            'nama_lengkap': 'Petugas RPL',
            'department': self.department.id,
            'password': 'password123'
        }

        url = reverse('user-petugas')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Petugas berhasil dibuat.')
        self.assertEqual(response.data['data']['username'], 'petugas_rpl')
        self.assertEqual(response.data['data']['role'], 'petugas')
        self.assertEqual(response.data['data']['is_verified'], True)
        
        # Verify user created in database
        user = User.objects.get(username='petugas_rpl')
        self.assertEqual(user.role, User.Role.PETUGAS)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_verified)

    def test_create_petugas_unauthorized(self):
        """User tanpa auth tidak bisa membuat petugas"""
        data = {
            'username': 'petugas_unauth',
            'email': 'petugas@smk-2sbg.sch.id',
            'nama_lengkap': 'Petugas Unauthorized',
            'department': self.department.id,
            'password': 'password123'
        }

        url = reverse('user-petugas')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_petugas_forbidden_for_peminjam(self):
        """Peminjam tidak bisa membuat petugas"""
        self.client.force_authenticate(user=self.peminjam)
        
        data = {
            'username': 'petugas_forbidden',
            'email': 'petugas@smk-2sbg.sch.id',
            'nama_lengkap': 'Petugas Forbidden',
            'department': self.department.id,
            'password': 'password123'
        }

        url = reverse('user-petugas')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_petugas_duplicate_username(self):
        """Username harus unik"""
        self.client.force_authenticate(user=self.admin)
        
        # Create existing user (peminjam needs complete fields)
        User.objects.create_user(
            username='existing_user',
            email='existing@smk-2sbg.sch.id',
            password='pass123',
            role=User.Role.PEMINJAM,
            nis='99991',
            nama_lengkap='Existing User',
            kelas='X RPL',
            department=self.department
        )

        data = {
            'username': 'existing_user',
            'email': 'new@smk-2sbg.sch.id',
            'nama_lengkap': 'Existing User',
            'department': self.department.id,
            'password': 'password123'
        }

        url = reverse('user-petugas')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_create_petugas_duplicate_email(self):
        """Email harus unik"""
        self.client.force_authenticate(user=self.admin)
        
        # Create existing user (peminjam needs complete fields)
        User.objects.create_user(
            username='unique_user',
            email='duplicate@smk-2sbg.sch.id',
            password='pass123',
            role=User.Role.PEMINJAM,
            nis='99992',
            nama_lengkap='Unique User',
            kelas='XI RPL',
            department=self.department
        )

        data = {
            'username': 'new_user',
            'email': 'duplicate@smk-2sbg.sch.id',
            'nama_lengkap': 'Duplicate Email',
            'department': self.department.id,
            'password': 'password123'
        }

        url = reverse('user-petugas')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_create_petugas_invalid_email_domain(self):
        """Email harus domain @smk-2sbg.sch.id"""
        self.client.force_authenticate(user=self.admin)
        
        data = {
            'username': 'petugas_invalid',
            'email': 'petugas@gmail.com',
            'nama_lengkap': 'Petugas Invalid',
            'department': self.department.id,
            'password': 'password123'
        }

        url = reverse('user-petugas')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('email', response.data.get('errors', {}))

    def test_create_petugas_short_password(self):
        """Password minimal 6 karakter"""
        self.client.force_authenticate(user=self.admin)
        
        data = {
            'username': 'petugas_short',
            'email': 'petugas2@smk-2sbg.sch.id',
            'nama_lengkap': 'Petugas Short',
            'department': self.department.id,
            'password': '12345'
        }

        url = reverse('user-petugas')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_create_petugas_missing_fields(self):
        """Semua field required harus diisi"""
        self.client.force_authenticate(user=self.admin)
        
        data = {
            'username': 'petugas_incomplete',
            # Missing: email, nama_lengkap, department, password
        }

        url = reverse('user-petugas')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_create_petugas_response_format(self):
        """Response format sesuai standar"""
        self.client.force_authenticate(user=self.admin)
        
        data = {
            'username': 'petugas_format',
            'email': 'format@smk-2sbg.sch.id',
            'nama_lengkap': 'Petugas Format',
            'department': self.department.id,
            'password': 'password123'
        }

        url = reverse('user-petugas')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Check response structure
        self.assertIn('success', response.data)
        self.assertIn('message', response.data)
        self.assertIn('data', response.data)
        
        # Check data structure
        data_response = response.data['data']
        self.assertIn('id', data_response)
        self.assertIn('username', data_response)
        self.assertIn('email', data_response)
        self.assertIn('role', data_response)
        self.assertIn('is_verified', data_response)
        
        # Password should NOT be in response
        self.assertNotIn('password', data_response)
