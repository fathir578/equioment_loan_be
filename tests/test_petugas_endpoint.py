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

    # ------------------------------------------------------------
    # GET /api/v1/users/petugas/ TESTS
    # ------------------------------------------------------------

    def test_get_petugas_list_success(self):
        """Admin berhasil mendapatkan list petugas"""
        self.client.force_authenticate(user=self.admin)
        
        # Create some petugas users
        User.objects.create_user(
            username='petugas_1',
            email='petugas1@smk-2sbg.sch.id',
            password='pass123',
            role=User.Role.PETUGAS,
            is_staff=True,
            is_verified=True,
            nama_lengkap='Petugas Satu',
            department=self.department
        )
        User.objects.create_user(
            username='petugas_2',
            email='petugas2@smk-2sbg.sch.id',
            password='pass123',
            role=User.Role.PETUGAS,
            is_staff=True,
            is_verified=True,
            nama_lengkap='Petugas Dua',
            department=self.department
        )

        url = reverse('user-petugas')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 2)
        self.assertEqual(len(response.data['data']['results']), 2)

    def test_get_petugas_list_search_username(self):
        """Search petugas by username"""
        self.client.force_authenticate(user=self.admin)
        
        User.objects.create_user(
            username='petugas_rpl',
            email='rpl@smk-2sbg.sch.id',
            password='pass123',
            role=User.Role.PETUGAS,
            is_staff=True,
            is_verified=True,
            nama_lengkap='Petugas RPL',
            department=self.department
        )
        User.objects.create_user(
            username='petugas_tki',
            email='tki@smk-2sbg.sch.id',
            password='pass123',
            role=User.Role.PETUGAS,
            is_staff=True,
            is_verified=True,
            nama_lengkap='Petugas TKI',
            department=self.department
        )

        url = reverse('user-petugas')
        response = self.client.get(url, {'search': 'rpl'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(response.data['data']['results'][0]['username'], 'petugas_rpl')

    def test_get_petugas_list_search_nama_lengkap(self):
        """Search petugas by nama_lengkap"""
        self.client.force_authenticate(user=self.admin)
        
        User.objects.create_user(
            username='petugas_abc',
            email='abc@smk-2sbg.sch.id',
            password='pass123',
            role=User.Role.PETUGAS,
            is_staff=True,
            is_verified=True,
            nama_lengkap='Ahmad Budi',
            department=self.department
        )
        User.objects.create_user(
            username='petugas_xyz',
            email='xyz@smk-2sbg.sch.id',
            password='pass123',
            role=User.Role.PETUGAS,
            is_staff=True,
            is_verified=True,
            nama_lengkap='Budi Santoso',
            department=self.department
        )

        url = reverse('user-petugas')
        response = self.client.get(url, {'search': 'budi'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 2)

    def test_get_petugas_list_filter_department(self):
        """Filter petugas by department"""
        self.client.force_authenticate(user=self.admin)
        
        # Create another department
        dept_tki, _ = Department.objects.get_or_create(
            kode='TKI',
            defaults={'nama': 'Teknik Komputer dan Informatika'}
        )
        
        User.objects.create_user(
            username='petugas_rpl',
            email='rpl@smk-2sbg.sch.id',
            password='pass123',
            role=User.Role.PETUGAS,
            is_staff=True,
            is_verified=True,
            nama_lengkap='Petugas RPL',
            department=self.department
        )
        User.objects.create_user(
            username='petugas_tki',
            email='tki@smk-2sbg.sch.id',
            password='pass123',
            role=User.Role.PETUGAS,
            is_staff=True,
            is_verified=True,
            nama_lengkap='Petugas TKI',
            department=dept_tki
        )

        url = reverse('user-petugas')
        response = self.client.get(url, {'department': self.department.id}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 1)
        self.assertEqual(response.data['data']['results'][0]['username'], 'petugas_rpl')

    def test_get_petugas_list_pagination(self):
        """Pagination with page_size param"""
        self.client.force_authenticate(user=self.admin)
        
        # Create 10 petugas users
        for i in range(10):
            User.objects.create_user(
                username=f'petugas_{i}',
                email=f'petugas{i}@smk-2sbg.sch.id',
                password='pass123',
                role=User.Role.PETUGAS,
                is_staff=True,
                is_verified=True,
                nama_lengkap=f'Petugas {i}',
                department=self.department
            )

        url = reverse('user-petugas')
        response = self.client.get(url, {'page_size': '3', 'page': '1'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 10)
        self.assertEqual(len(response.data['data']['results']), 3)
        self.assertEqual(response.data['data']['page'], 1)
        self.assertEqual(response.data['data']['pages'], 4)

    def test_get_petugas_list_unauthorized(self):
        """User tanpa auth tidak bisa list petugas"""
        url = reverse('user-petugas')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_petugas_list_forbidden_for_peminjam(self):
        """Peminjam tidak bisa list petugas"""
        self.client.force_authenticate(user=self.peminjam)
        
        url = reverse('user-petugas')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_petugas_list_empty(self):
        """List petugas kosong"""
        self.client.force_authenticate(user=self.admin)
        
        # Delete all petugas
        User.objects.filter(role=User.Role.PETUGAS).delete()

        url = reverse('user-petugas')
        response = self.client.get(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['count'], 0)
        self.assertEqual(len(response.data['data']['results']), 0)
