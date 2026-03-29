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

    # ------------------------------------------------------------
    # PUT /api/v1/users/petugas/{id}/ TESTS
    # ------------------------------------------------------------

    def test_update_petugas_success(self):
        """Admin berhasil update data petugas"""
        self.client.force_authenticate(user=self.admin)
        
        # Create petugas user
        petugas = User.objects.create_user(
            username='petugas_old',
            email='old@smk-2sbg.sch.id',
            password='oldpass123',
            role=User.Role.PETUGAS,
            is_staff=True,
            is_verified=True,
            nama_lengkap='Petugas Old',
            department=self.department
        )

        url = reverse('user-petugas-detail', kwargs={'pk': petugas.id})
        data = {
            'username': 'petugas_new',
            'email': 'new@smk-2sbg.sch.id',
            'nama_lengkap': 'Petugas New',
            'department': self.department.id
        }
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Petugas berhasil diupdate.')
        self.assertEqual(response.data['data']['username'], 'petugas_new')
        self.assertEqual(response.data['data']['email'], 'new@smk-2sbg.sch.id')
        
        # Verify password still works
        petugas.refresh_from_db()
        self.assertTrue(petugas.check_password('oldpass123'))

    def test_update_petugas_with_password(self):
        """Admin update petugas dengan password baru"""
        self.client.force_authenticate(user=self.admin)
        
        petugas = User.objects.create_user(
            username='petugas_pass',
            email='pass@smk-2sbg.sch.id',
            password='oldpass123',
            role=User.Role.PETUGAS,
            is_staff=True,
            is_verified=True,
            nama_lengkap='Petugas Pass',
            department=self.department
        )

        url = reverse('user-petugas-detail', kwargs={'pk': petugas.id})
        data = {
            'username': 'petugas_pass',
            'email': 'pass@smk-2sbg.sch.id',
            'nama_lengkap': 'Petugas Pass',
            'department': self.department.id,
            'password': 'newpass456'
        }
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify new password works
        petugas.refresh_from_db()
        self.assertTrue(petugas.check_password('newpass456'))

    def test_update_petugas_short_password(self):
        """Password minimal 6 karakter"""
        self.client.force_authenticate(user=self.admin)
        
        petugas = User.objects.create_user(
            username='petugas_short',
            email='short@smk-2sbg.sch.id',
            password='oldpass123',
            role=User.Role.PETUGAS,
            is_staff=True,
            is_verified=True,
            nama_lengkap='Petugas Short',
            department=self.department
        )

        url = reverse('user-petugas-detail', kwargs={'pk': petugas.id})
        data = {
            'username': 'petugas_short',
            'email': 'short@smk-2sbg.sch.id',
            'nama_lengkap': 'Petugas Short',
            'department': self.department.id,
            'password': '12345'
        }
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_update_petugas_invalid_email_domain(self):
        """Email harus domain @smk-2sbg.sch.id"""
        self.client.force_authenticate(user=self.admin)
        
        petugas = User.objects.create_user(
            username='petugas_email',
            email='email@smk-2sbg.sch.id',
            password='pass123',
            role=User.Role.PETUGAS,
            is_staff=True,
            is_verified=True,
            nama_lengkap='Petugas Email',
            department=self.department
        )

        url = reverse('user-petugas-detail', kwargs={'pk': petugas.id})
        data = {
            'username': 'petugas_email',
            'email': 'email@gmail.com',
            'nama_lengkap': 'Petugas Email',
            'department': self.department.id
        }
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_update_petugas_unauthorized(self):
        """User tanpa auth tidak bisa update petugas"""
        petugas = User.objects.create_user(
            username='petugas_unauth',
            email='unauth@smk-2sbg.sch.id',
            password='pass123',
            role=User.Role.PETUGAS,
            is_staff=True,
            is_verified=True,
            nama_lengkap='Petugas Unauth',
            department=self.department
        )

        url = reverse('user-petugas-detail', kwargs={'pk': petugas.id})
        data = {
            'username': 'petugas_new',
            'email': 'new@smk-2sbg.sch.id',
            'nama_lengkap': 'Petugas New',
            'department': self.department.id
        }
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_petugas_forbidden_for_peminjam(self):
        """Peminjam tidak bisa update petugas"""
        self.client.force_authenticate(user=self.peminjam)
        
        petugas = User.objects.create_user(
            username='petugas_forbidden',
            email='forbidden@smk-2sbg.sch.id',
            password='pass123',
            role=User.Role.PETUGAS,
            is_staff=True,
            is_verified=True,
            nama_lengkap='Petugas Forbidden',
            department=self.department
        )

        url = reverse('user-petugas-detail', kwargs={'pk': petugas.id})
        data = {
            'username': 'petugas_new',
            'email': 'new@smk-2sbg.sch.id',
            'nama_lengkap': 'Petugas New',
            'department': self.department.id
        }
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_non_petugas_user(self):
        """Tidak bisa update user yang bukan petugas"""
        self.client.force_authenticate(user=self.admin)
        
        # Create peminjam user
        peminjam = User.objects.create_user(
            username='999999',
            email='peminjam999@smk-2sbg.sch.id',
            password='pass123',
            role=User.Role.PEMINJAM,
            nis='999999',
            nama_lengkap='Peminjam Test',
            kelas='X RPL',
            department=self.department
        )

        url = reverse('user-petugas-detail', kwargs={'pk': peminjam.id})
        data = {
            'username': 'peminjam_new',
            'email': 'peminjam999@smk-2sbg.sch.id',
            'nama_lengkap': 'Peminjam New',
            'department': self.department.id
        }
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'User bukan petugas.')

    # ------------------------------------------------------------
    # DELETE /api/v1/users/petugas/{id}/ TESTS
    # ------------------------------------------------------------

    def test_delete_petugas_success(self):
        """Admin berhasil hapus petugas"""
        self.client.force_authenticate(user=self.admin)
        
        petugas = User.objects.create_user(
            username='petugas_delete',
            email='delete@smk-2sbg.sch.id',
            password='pass123',
            role=User.Role.PETUGAS,
            is_staff=True,
            is_verified=True,
            nama_lengkap='Petugas Delete',
            department=self.department
        )

        url = reverse('user-petugas-detail', kwargs={'pk': petugas.id})
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Petugas berhasil dihapus.')
        
        # Verify user deleted
        self.assertFalse(User.objects.filter(id=petugas.id).exists())

    def test_delete_petugas_unauthorized(self):
        """User tanpa auth tidak bisa hapus petugas"""
        petugas = User.objects.create_user(
            username='petugas_del_unauth',
            email='delunauth@smk-2sbg.sch.id',
            password='pass123',
            role=User.Role.PETUGAS,
            is_staff=True,
            is_verified=True,
            nama_lengkap='Petugas Del Unauth',
            department=self.department
        )

        url = reverse('user-petugas-detail', kwargs={'pk': petugas.id})
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_delete_petugas_forbidden_for_peminjam(self):
        """Peminjam tidak bisa hapus petugas"""
        self.client.force_authenticate(user=self.peminjam)
        
        petugas = User.objects.create_user(
            username='petugas_del_forbidden',
            email='delforbidden@smk-2sbg.sch.id',
            password='pass123',
            role=User.Role.PETUGAS,
            is_staff=True,
            is_verified=True,
            nama_lengkap='Petugas Del Forbidden',
            department=self.department
        )

        url = reverse('user-petugas-detail', kwargs={'pk': petugas.id})
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_non_petugas_user(self):
        """Tidak bisa delete user yang bukan petugas"""
        self.client.force_authenticate(user=self.admin)
        
        # Create peminjam user
        peminjam = User.objects.create_user(
            username='888888',
            email='peminjam888@smk-2sbg.sch.id',
            password='pass123',
            role=User.Role.PEMINJAM,
            nis='888888',
            nama_lengkap='Peminjam Delete',
            kelas='XI RPL',
            department=self.department
        )

        url = reverse('user-petugas-detail', kwargs={'pk': peminjam.id})
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'User bukan petugas.')
        
        # Verify user not deleted
        self.assertTrue(User.objects.filter(id=peminjam.id).exists())

    def test_delete_petugas_has_related_returns(self):
        """Tidak bisa delete petugas yang masih punya data pengembalian"""
        from apps.returns.models import Return
        from apps.loans.models import Loan
        from datetime import date
        
        self.client.force_authenticate(user=self.admin)
        
        petugas = User.objects.create_user(
            username='petugas_with_return',
            email='withreturn@smk-2sbg.sch.id',
            password='pass123',
            role=User.Role.PETUGAS,
            is_staff=True,
            is_verified=True,
            nama_lengkap='Petugas With Return',
            department=self.department
        )
        
        # Create a loan and return processed by this petugas
        siswa = User.objects.create_user(
            username='999998',
            email='siswa999@smk-2sbg.sch.id',
            password='pass123',
            role=User.Role.PEMINJAM,
            nis='999998',
            nama_lengkap='Siswa Test',
            kelas='X RPL',
            department=self.department
        )
        
        loan = Loan.objects.create(
            user=siswa,
            loan_date=date.today(),
            due_date=date.today(),
            status='returned',
            approved_by=petugas
        )
        
        Return.objects.create(
            loan=loan,
            return_date=date.today(),
            processed_by=petugas
        )

        url = reverse('user-petugas-detail', kwargs={'pk': petugas.id})
        response = self.client.delete(url, format='json')

        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertFalse(response.data['success'])
        self.assertIn('masih memiliki data terkait', response.data['message'])
        
        # Verify user not deleted
        self.assertTrue(User.objects.filter(id=petugas.id).exists())
