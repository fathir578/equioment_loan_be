2# Dokumentasi API Peminjaman Alat
**Base URL:** `http://localhost:8000/api/v1/`

Dokumentasi interaktif (Swagger UI) dapat diakses di: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)

---

## 1. Autentikasi (`/auth/`)
Digunakan untuk manajemen akun dan sesi login.

| Endpoint | Method | Hak Akses | Deskripsi |
| :--- | :--- | :--- | :--- |
| `/auth/register/` | POST | Public | Registrasi akun siswa baru (default role: peminjam). |
| `/auth/login/` | POST | Public | Login untuk mendapatkan Access & Refresh Token (JWT). |
| `/auth/refresh/` | POST | Authenticated | Memperbarui Access Token menggunakan Refresh Token. |
| `/auth/logout/` | POST | Authenticated | Blacklist Refresh Token agar tidak bisa digunakan lagi. |
| `/auth/profile/` | GET | Authenticated | Mengambil data profil user yang sedang login. |

---

## 2. Manajemen User (`/users/`)
Pengelolaan data pengguna sistem.

| Endpoint | Method | Hak Akses | Deskripsi |
| :--- | :--- | :--- | :--- |
| `/users/` | GET | Admin | Melihat daftar semua user (bisa filter role & status). |
| `/users/{id}/` | GET | Admin | Melihat detail user tertentu. |
| `/users/{id}/` | PATCH/PUT| Admin | Mengupdate data user atau menonaktifkan akun. |

---

## 3. Kategori Alat (`/categories/`)
Pengelompokan alat sekolah.

| Endpoint | Method | Hak Akses | Deskripsi |
| :--- | :--- | :--- | :--- |
| `/categories/` | GET | Authenticated | Melihat daftar semua kategori. |
| `/categories/` | POST | Admin/Petugas | Menambah kategori baru. |
| `/categories/{id}/` | PATCH/PUT| Admin/Petugas | Mengupdate nama atau deskripsi kategori. |

---

## 4. Daftar Alat (`/tools/`)
Manajemen stok dan kondisi alat.

| Endpoint | Method | Hak Akses | Deskripsi |
| :--- | :--- | :--- | :--- |
| `/tools/` | GET | Authenticated | Melihat daftar alat (bisa search nama & filter kategori). |
| `/tools/` | POST | Admin/Petugas | Menambah alat baru ke sistem. |
| `/tools/{id}/` | GET | Authenticated | Melihat detail spesifikasi dan stok alat. |
| `/tools/{id}/` | PATCH/PUT| Admin/Petugas | Update stok, kondisi, atau status aktif alat. |

---

## 5. Peminjaman (`/loans/`)
Proses pengajuan dan persetujuan pinjam alat.

| Endpoint | Method | Hak Akses | Deskripsi |
| :--- | :--- | :--- | :--- |
| `/loans/` | GET | Owner/Admin | Siswa melihat pinjamannya, Admin melihat semua. |
| `/loans/` | POST | Peminjam | Mengajukan pinjaman baru (Memanggil SP `sp_create_loan`). |
| `/loans/{id}/approve/` | POST | Admin/Petugas | Menyetujui pengajuan pinjaman (Trigger update stok). |
| `/loans/{id}/reject/` | POST | Admin/Petugas | Menolak pengajuan pinjaman. |

---

## 6. Pengembalian (`/returns/`)
Proses pengembalian alat dan denda.

| Endpoint | Method | Hak Akses | Deskripsi |
| :--- | :--- | :--- | :--- |
| `/returns/` | GET | Admin/Petugas | Melihat riwayat pengembalian alat. |
| `/returns/` | POST | Admin/Petugas | Memproses pengembalian (Memanggil SP `sp_process_return`). |
| `/returns/{id}/` | GET | Admin/Petugas | Melihat detail denda dan kondisi alat saat kembali. |

---

## 7. Audit Log (`/logs/`)
Catatan aktivitas sistem untuk keamanan.

| Endpoint | Method | Hak Akses | Deskripsi |
| :--- | :--- | :--- | :--- |
| `/logs/` | GET | Admin | Melihat log aktivitas (siapa, melakukan apa, kapan, IP). |
| `/logs/{id}/` | GET | Admin | Melihat detail narasi aktivitas tertentu. |

---

## Format Response Standar
Semua API (kecuali list standar DRF) menggunakan format:
```json
{
    "success": true,
    "message": "Pesan deskriptif",
    "data": { ... }
}
```

## Akun Demo (Development)
*   **Admin:** `admin` / `Password123!`
*   **Siswa:** `budi` / `Password123!`
