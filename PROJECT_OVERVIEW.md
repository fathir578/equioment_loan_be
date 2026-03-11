# Laporan Arsitektur & Implementasi Sistem: Backend Peminjaman Alat
**Dokumen Referensi Teknis Komprehensif — UKK RPL 2025/2026**

---

## 1. Pendahuluan
Sistem ini dirancang sebagai solusi backend yang tangguh untuk manajemen peminjaman alat di lingkungan sekolah. Fokus utama pengembangan adalah pada **Integritas Data** (menggunakan logika sisi database) dan **Keamanan Berlapis** (menggunakan standar industri seperti JWT, Argon2, dan Throttling). Dokumen ini berfungsi sebagai peta jalan teknis untuk memahami seluruh komponen sistem.

---

## 2. Struktur Proyek & Coding Guidelines
Proyek ini mengikuti pola arsitektur **Modular Monolith** yang diatur dalam folder `apps/`. Pemisahan ini memastikan kode mudah dibaca, diuji, dan dikembangkan di masa depan.

### 2.1 Direktori Utama
*   `config/`: Berisi konfigurasi global Django.
    *   `settings.py`: Jantung konfigurasi (Database, JWT, Password Hashers, Middleware, Throttling).
    *   `urls.py`: Routing utama yang menghubungkan semua modul API.
*   `core/`: Berisi logika yang digunakan bersama oleh semua aplikasi.
    *   `permissions.py`: Definisi hak akses RBAC (Admin, Petugas, Peminjam).
    *   `pagination.py`: Standar format data per halaman.
    *   `middleware.py`: Custom middleware untuk audit trail (IP & User-Agent).
*   `apps/`: Folder berisi modul bisnis mandiri (users, tools, loans, returns, activity_logs).

---

## 3. Implementasi Kriteria Teknis & Keamanan

### 🔐 3.1 Authentication & Authorization (WAJIB)
Sistem menggunakan **JSON Web Token (JWT)** untuk autentikasi stateless.
*   **Implementasi Login:** `apps/users/views.py` -> `MyTokenObtainPairView`.
*   **Logout & Blacklist:** User dapat logout secara aman dengan mem-blacklist Refresh Token.
*   **Authorization (RBAC):** Izin akses didefinisikan secara deklaratif di `core/permissions.py`.

### 🛡️ 3.2 Password Hashing (Advanced)
Untuk proteksi data pengguna, sistem menggunakan **Argon2**, yang merupakan algoritma hashing paling aman saat ini, jauh lebih unggul dibandingkan MD5 atau SHA1.

### 🚦 3.3 Rate Limiting / Throttling (PENTING)
Mencegah serangan brute force dan penyalahgunaan API.
*   **Logika:** 
    *   `login`: 5 request/menit khusus untuk endpoint `/api/auth/login/`.
    *   `user`: 100 request/menit untuk user terautentikasi.

### 📄 3.4 Pagination (PENTING)
Memastikan performa aplikasi tetap cepat meskipun data mencapai ribuan.
*   **Lokasi:** `core/pagination.py` -> kelas `StandardPagination`.

---

## 4. Fitur Tambahan Unggulan (Advanced Features)

### 📊 4.1 Dashboard Analytics API
Menyediakan endpoint ringkasan data untuk Admin.
*   **Lokasi:** `apps/activity_logs/views.py` -> `DashboardStatsView`.

### 📁 4.2 Export Laporan (CSV)
Memungkinkan Admin mengunduh laporan peminjaman dalam format Excel-ready.
*   **Lokasi:** `apps/loans/views.py` -> `ExportLoansCSVView`.

### 📱 4.3 Otomatisasi QR Code (Safe & Unique)
Sistem secara otomatis men-generate QR Code menggunakan **UUID4** (Universally Unique Identifier) yang tidak dapat diprediksi oleh pihak luar.
*   **Lokasi:** `core/utils.py` -> `generate_qr_token`.

### 🧪 4.4 Automated Logic Testing
Skrip pengujian otomatis untuk menjamin validitas database trigger dan stored procedure.
*   **Lokasi:** `tests/test_logic.py`.

---

## 5. Skenario Pengujian (User Acceptance Test - UAT)

| No | Skenario | Langkah | Hasil yang Diharapkan |
| :--- | :--- | :--- | :--- |
| 1 | Registrasi Siswa | POST `/api/auth/register/` | Akun dibuat dengan password ter-hash Argon2. |
| 2 | Login | POST `/api/auth/login/` | Mendapatkan access & refresh token. |
| 3 | Audit Trail | Lakukan aksi POST/PUT | Log tercatat di DB beserta IP & User-Agent. |
| 4 | Logout | POST `/api/auth/logout/` | Refresh token di-blacklist, tidak bisa dipakai lagi. |
| 5 | Tambah Alat | POST `/api/tools/` (Admin) | Alat tersimpan, file QR Code terbuat otomatis. |
| 6 | Pengajuan Pinjam | POST `/api/loans/` | Memanggil `sp_create_loan`. Transaksi DB menjamin integritas stok. |
| 7 | Pengembalian | POST `/api/returns/` | Prosedur menghitung denda otomatis di level DB. |

---

## 6. Arsitektur Database & Logika SQL (WAJIB DARI SOAL)

### 6.1 Stored Procedures (`sql/stored_procedures.sql`)
*   **`sp_create_loan`**: Menjamin atomisitas peminjaman multi-item dengan `START TRANSACTION`.
*   **`sp_process_return`**: Menghitung denda secara otomatis di sisi server database.

### 6.2 Triggers (`sql/triggers.sql`)
*   **Stok Otomatis**: Stok berkurang/bertambah otomatis saat status loan berubah.
*   **Validasi Keamanan**: Mencegah approval ilegal di level database.

---
**Dibuat oleh:** Sistem Backend UKK
**Status:** Produksi / Siap Pakai / v1.1.0
