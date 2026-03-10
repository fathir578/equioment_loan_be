# Laporan Arsitektur & Implementasi Sistem: Backend Peminjaman Alat
**Dokumen Referensi Teknis Komprehensif — UKK RPL 2025/2026**

---

## 1. Pendahuluan
Sistem ini dirancang sebagai solusi backend yang tangguh untuk manajemen peminjaman alat di lingkungan sekolah. Fokus utama pengembangan adalah pada **Integritas Data** (menggunakan logika sisi database) dan **Keamanan** (menggunakan standar industri seperti JWT dan Throttling). Dokumen ini berfungsi sebagai peta jalan teknis untuk memahami seluruh komponen sistem.

---

## 2. Struktur Proyek & Coding Guidelines
Proyek ini mengikuti pola arsitektur **Modular Monolith** yang diatur dalam folder `apps/`. Pemisahan ini memastikan kode mudah dibaca, diuji, dan dikembangkan di masa depan.

### 2.1 Direktori Utama
*   `config/`: Berisi konfigurasi global Django.
    *   `settings.py`: Jantung konfigurasi (Database, JWT, Middleware, Throttling).
    *   `urls.py`: Routing utama yang menghubungkan semua modul API.
*   `core/`: Berisi logika yang digunakan bersama oleh semua aplikasi.
    *   `permissions.py`: Definisi hak akses RBAC (Admin, Petugas, Peminjam).
    *   `pagination.py`: Standar format data per halaman.
*   `apps/`: Folder berisi modul bisnis mandiri (users, tools, loans, returns, dashboard).

---

## 3. Implementasi Kriteria Teknis (Detail Kode)

### 🔐 3.1 Authentication & Authorization (WAJIB)
Sistem menggunakan **JSON Web Token (JWT)** untuk autentikasi stateless.
*   **Implementasi Login:** `apps/users/views.py` -> `MyTokenObtainPairView`.
*   **Authorization (RBAC):** Izin akses didefinisikan di `core/permissions.py`.

### 🚦 3.2 Rate Limiting / Throttling (PENTING)
Mencegah serangan brute force dan penyalahgunaan API.
*   **Logika:** 
    *   `login`: 5 request/menit khusus untuk endpoint `/auth/login/`.

### 📄 3.3 Pagination (PENTING)
Memastikan performa aplikasi tetap cepat meskipun data mencapai ribuan.
*   **Lokasi:** `core/pagination.py` -> kelas `StandardPagination`.

---

## 4. Fitur Tambahan Unggulan (Advanced Features)

### 📊 4.1 Dashboard Analytics API
Menyediakan endpoint ringkasan data untuk Admin.
*   **Lokasi:** `apps/activity_logs/views.py` -> `DashboardStatsView`.
*   **Output:** Total user, alat, stok, status loan, dan denda keuangan.

### 📁 4.2 Export Laporan (CSV)
Memungkinkan Admin mengunduh laporan peminjaman dalam format Excel-ready.
*   **Lokasi:** `apps/loans/views.py` -> `ExportLoansCSVView`.

### 📱 4.3 Otomatisasi QR Code (Real-time)
Sistem secara otomatis men-generate file gambar fisik QR Code (.png) saat user atau alat baru dibuat.
*   **Lokasi:** Override method `save()` pada model di `apps/users/models.py` dan `apps/tools/models.py`.

### 🧪 4.4 Automated Logic Testing
Skrip pengujian otomatis untuk menjamin validitas database trigger dan stored procedure.
*   **Lokasi:** `tests/test_logic.py`.

---

## 5. Skenario Pengujian (User Acceptance Test - UAT)

Berikut adalah langkah-langkah pengujian untuk memverifikasi fungsionalitas sistem:

| No | Skenario | Langkah | Hasil yang Diharapkan |
| :--- | :--- | :--- | :--- |
| 1 | Registrasi Siswa | POST `/auth/register/` | Akun dibuat, file `user_{username}.png` muncul di folder media. |
| 2 | Login | POST `/auth/login/` | Mendapatkan token JWT. |
| 3 | Tambah Alat | POST `/tools/` (Admin) | Alat tersimpan, file `tool_{token}.png` terbuat otomatis. |
| 4 | Pengajuan Pinjam | POST `/loans/` (Siswa) | Memanggil `sp_create_loan`. Stok alat di-lock untuk transaksi. |
| 5 | Persetujuan | POST `/loans/{id}/approve/` | Trigger berjalan, stok alat berkurang di tabel `tools`. |
| 6 | Pengembalian Telat | POST `/returns/` | Prosedur menghitung selisih hari & mengisi kolom `total_fine`. |
| 7 | Download Laporan | GET `/loans/export/csv/` | File CSV terunduh dengan data peminjaman terbaru. |

---

## 6. Arsitektur Database & Logika SQL (WAJIB DARI SOAL)

### 6.1 Stored Procedures (`stored_procedures.sql`)
*   **`sp_create_loan`**: Menjamin atomisitas peminjaman multi-item.
*   **`sp_process_return`**: Menghitung denda secara otomatis di sisi server database.

### 6.2 Triggers (`triggers.sql`)
*   **Stok Otomatis**: Stok berkurang/bertambah tanpa campur tangan kode aplikasi.
*   **Validasi Keamanan**: Mencegah approval ilegal di level database.

---
**Dibuat oleh:** Sistem Backend UKK
**Status:** Produksi / Siap Pakai / v1.0.0
