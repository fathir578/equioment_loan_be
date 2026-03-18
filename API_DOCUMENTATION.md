# Dokumentasi API Peminjaman Alat (v2.0.0)
**Base URL:** `http://localhost:8000/api/v1/`

Dokumentasi interaktif (Swagger UI) dapat diakses di: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)

---

## 1. Autentikasi (`/auth/`)
Digunakan untuk manajemen akun dan sesi login.

| Endpoint | Method | Hak Akses | Deskripsi |
| :--- | :--- | :--- | :--- |
| `/auth/register/` | POST | Public | Registrasi Admin/Petugas (Wajib email sekolah). |
| `/auth/login/` | POST | Public | Login via Username (NIS untuk siswa) & Password. |
| `/auth/refresh/` | POST | Authenticated | Memperbarui Access Token. |
| `/auth/logout/` | POST | Authenticated | Blacklist Refresh Token. |
| `/auth/profile/` | GET | Authenticated | Mengambil data profil user yang sedang login. |

---

## 2. Manajemen User & Siswa (`/users/`)
Pengelolaan data pengguna sistem.

| Endpoint | Method | Hak Akses | Deskripsi |
| :--- | :--- | :--- | :--- |
| `/users/` | GET | Staff | Daftar user (Petugas dibatasi ke jurusannya). |
| `/users/peminjam/` | POST | Staff | [NEW v2.0.0] Daftarkan siswa baru (NIS, Kelas, Jurusan). |
| `/users/peminjam/` | GET | Staff | [NEW v2.0.0] Daftar siswa (Bisa filter ?dept=RPL&kelas=...). |
| `/users/{id}/verify/`| POST | Staff | [NEW v2.0.0] Verifikasi akun siswa. |
| `/users/pending/` | GET | Staff | [NEW v2.0.0] Daftar siswa yang menunggu verifikasi. |
| `/users/{id}/` | GET | Same Dept | Detail user tertentu. |

---

## 3. Jurusan / Departments (`/departments/`)
Manajemen data jurusan sekolah.

| Endpoint | Method | Hak Akses | Deskripsi |
| :--- | :--- | :--- | :--- |
| `/departments/` | GET | Authenticated | Melihat daftar semua jurusan. |
| `/departments/{id}/` | GET | Authenticated | Melihat detail jurusan tertentu. |

---

## 4. Daftar Alat (`/tools/`)
Manajemen stok dan kondisi alat per jurusan.

| Endpoint | Method | Hak Akses | Deskripsi |
| :--- | :--- | :--- | :--- |
| `/tools/` | GET | Authenticated | Daftar alat (Petugas dibatasi ke jurusannya). |
| `/tools/` | POST | Staff | Menambah alat baru ke sistem (bisa set jurusan). |
| `/tools/{id}/` | GET | Same Dept | Melihat detail spesifikasi dan stok alat. |
| `/tools/{id}/` | PATCH/PUT| Staff | Update stok, kondisi, atau status aktif alat. |

---

## 5. Peminjaman (`/loans/`)
Proses pengajuan dan persetujuan pinjam alat.

| Endpoint | Method | Hak Akses | Deskripsi |
| :--- | :--- | :--- | :--- |
| `/loans/` | GET | Owner/Staff | Siswa lihat miliknya, Staff lihat di jurusannya. |
| `/loans/` | POST | Peminjam | Mengajukan pinjaman baru (Memanggil SP). |
| `/loans/{id}/approve/` | POST | Staff | Menyetujui pinjaman (Trigger update stok). |
| `/loans/{id}/reject/` | POST | Staff | Menolak pengajuan pinjaman. |

---

## 6. Laporan Excel (`/reports/`) [NEW v2.0.0]
Generasi laporan untuk kebutuhan administrasi.

| Endpoint | Method | Hak Akses | Deskripsi |
| :--- | :--- | :--- | :--- |
| `/reports/{kode_dept}/`| GET | Authenticated | Download Laporan Excel per Jurusan (Semua Kelas & Per Tingkat). |

---

## Format Response Standar
```json
{
    "success": true,
    "message": "Pesan deskriptif",
    "data": { ... }
}
```

## Akun Demo (v2.0.0)
*   **Username:** `admin` (Admin Utama)
*   **Username Petugas:** `petugas_rpl` (Petugas Jurusan RPL)
*   **Username Siswa:** Pakai NIS yang didaftarkan.
