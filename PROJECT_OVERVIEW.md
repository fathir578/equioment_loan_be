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
    *   `wsgi.py` & `asgi.py`: Entry point untuk server produksi.
*   `core/`: Berisi logika yang digunakan bersama oleh semua aplikasi.
    *   `permissions.py`: Definisi hak akses RBAC (Admin, Petugas, Peminjam).
    *   `pagination.py`: Standar format data per halaman.
    *   `middleware.py`: Logika otomatis untuk mencatat aktivitas user (Audit Trail).
    *   `utils.py`: Fungsi pembantu (QR Code generator, success response formatter).
    *   `exceptions.py`: Penanganan error global agar format response selalu JSON.
*   `apps/`: Folder berisi modul bisnis mandiri.
    *   `users/`: Autentikasi dan manajemen profil.
    *   `categories/`: Klasifikasi jenis alat.
    *   `tools/`: Katalog inventaris alat.
    *   `loans/`: Transaksi peminjaman dan approval.
    *   `returns/`: Transaksi pengembalian dan kalkulasi denda.
    *   `activity_logs/`: Catatan audit sistem.

---

## 3. Implementasi Kriteria Teknis (Detail Kode)

### 🔐 3.1 Authentication & Authorization (WAJIB)
Sistem menggunakan **JSON Web Token (JWT)** untuk autentikasi stateless.
*   **Implementasi Login:** `apps/users/views.py` -> `MyTokenObtainPairView`.
*   **Custom Claims:** Kita menyisipkan `role` dan `username` ke dalam payload token di `apps/users/serializers.py` -> `MyTokenObtainPairSerializer`.
*   **Authorization (RBAC):** 
    *   Izin akses didefinisikan di `core/permissions.py`.
    *   Contoh: `IsAdminOrPetugas` digunakan pada endpoint `/tools/` agar hanya staf yang bisa mengubah data alat.
    *   `IsOwnerOrAdmin` digunakan pada `/loans/` agar siswa hanya bisa melihat datanya sendiri, sementara Admin bisa melihat semuanya.

### 🚦 3.2 Rate Limiting / Throttling (PENTING)
Mencegah serangan brute force dan penyalahgunaan API.
*   **Lokasi:** `config/settings.py` pada bagian `REST_FRAMEWORK`.
*   **Logika:** 
    *   `anon`: 20 request/menit untuk user publik.
    *   `user`: 100 request/menit untuk user terdaftar.
    *   `login`: 5 request/menit khusus untuk endpoint `/auth/login/`.

### 📄 3.3 Pagination (PENTING)
Memastikan performa aplikasi tetap cepat meskipun data mencapai ribuan.
*   **Lokasi:** `core/pagination.py` -> kelas `StandardPagination`.
*   **Format:** Menghasilkan metadata seperti `total_pages`, `current_page`, dan `results`.
*   **Default:** 10 item per halaman, dapat diatur via query param `?page_size=`.

### ✅ 3.4 Input Validation (WAJIB)
Validasi dilakukan di tiga lapis (Triple Layer Validation):
1.  **Serializer Layer:** Validasi tipe data dan format di `apps/*/serializers.py`.
2.  **Model Layer:** Validasi logika bisnis di `apps/loans/models.py` (method `clean()`) untuk memastikan tanggal kembali tidak mendahului tanggal pinjam.
3.  **Database Layer:** Constraint `CHECK` dan Trigger di SQL untuk memastikan integritas data (misal: stok tidak boleh negatif).

---

## 4. Arsitektur Database & Logika SQL (WAJIB DARI SOAL)

Sistem memindahkan beban logika berat ke database untuk menjamin konsistensi data yang mutlak.

### 4.1 Tabel Utama & Relasi
1.  **`users`**: PK `id`, `username`, `email`, `password`, `role`, `qr_token`.
2.  **`categories`**: PK `id`, `name`.
3.  **`tools`**: PK `id`, FK `category_id`, `name`, `stock_total`, `stock_available`, `condition`.
4.  **`loans`**: PK `id`, FK `user_id`, FK `approved_by`, `loan_date`, `due_date`, `status`.
5.  **`loan_items`**: PK `id`, FK `loan_id`, FK `tool_id`, `quantity`.
6.  **`returns`**: PK `id`, FK `loan_id`, FK `processed_by`, `return_date`, `total_fine`.

### 4.2 Stored Procedures (`stored_procedures.sql`)
*   **`sp_create_loan`**:
    *   Menerima data user, tanggal, dan JSON berisi daftar alat.
    *   **Algoritma:** 
        1. Mulai Transaksi.
        2. Insert ke `loans`.
        3. Loop melalui JSON alat.
        4. Cek stok di tabel `tools` menggunakan `FOR UPDATE` (locking row).
        5. Jika stok cukup, insert ke `loan_items`.
        6. Jika gagal, `ROLLBACK` semua. Jika sukses, `COMMIT`.
*   **`sp_process_return`**:
    *   Menghitung denda otomatis menggunakan fungsi `fn_calculate_fine`.
    *   Mendukung pengembalian parsial (sebagian).

### 4.3 Triggers (`triggers.sql`)
*   **`trg_decrease_stock_on_approve`**: Saat status loan berubah jadi 'approved', stok di tabel `tools` otomatis berkurang.
*   **`trg_restore_stock_on_reject`**: Jika ditolak, stok dikembalikan.
*   **`trg_process_return_item`**: Saat alat kembali, stok bertambah otomatis. Jika kondisi kembali adalah 'rusak', trigger ini bisa menurunkan status kondisi alat di katalog.
*   **`trg_validate_loan_approver`**: Memastikan peminjam tidak bisa menyetujui (approve) pinjamannya sendiri.

---

## 5. Alur Kerja Sistem (Workflows)

### 5.1 Siklus Peminjaman
1.  **Registrasi/Login**: User mendapatkan token JWT.
2.  **Pengajuan**: User memanggil `POST /api/v1/loans/`. Logic dijalankan oleh `sp_create_loan`. Status: `pending`.
3.  **Verifikasi**: Petugas mengecek ketersediaan fisik alat.
4.  **Approval**: Petugas memanggil `POST /api/v1/loans/{id}/approve/`. Trigger database mengurangi stok secara otomatis. Status: `approved`.

### 5.2 Siklus Pengembalian
1.  **Penyerahan**: Siswa mengembalikan alat ke petugas.
2.  **Input Data**: Petugas memanggil `POST /api/v1/returns/`.
3.  **Kalkulasi**: Database menghitung selisih hari. Jika `hari > 0`, denda dihitung otomatis.
4.  **Update**: Stok alat bertambah otomatis via trigger. Status: `returned`.

---

## 6. Audit Trail & Log Aktivitas (Audit System)

Sistem mencatat setiap jejak langkah user untuk keamanan:
*   **Middleware Log**: Di `core/middleware.py`, sistem menangkap setiap request `POST`, `PUT`, `PATCH`, dan `DELETE`. Informasi yang dicatat meliputi: User ID, URL endpoint, Method, IP Address, dan Timestamp.
*   **Database Log**: Trigger `trg_log_new_user` mencatat langsung ke tabel `activity_logs` setiap kali ada baris baru di tabel `users`.
*   **Monitoring**: Admin dapat memantau log ini di `api/v1/logs/`.

---

## 7. Keamanan & Enkripsi
*   **Password Hashing**: Menggunakan `django.contrib.auth.hashers`. Password tidak pernah disimpan dalam bentuk teks biasa, melainkan di-hash menggunakan algoritma **PBKDF2** dengan salt yang unik untuk setiap user.
*   **CORS Policy**: Dikonfigurasi di `config/settings.py` untuk mengizinkan hanya domain frontend tertentu yang bisa mengakses API.
*   **JWT Security**: Token memiliki masa kadaluarsa (Access: 60 menit, Refresh: 7 hari). Jika token bocor, akses akan otomatis tertutup setelah waktu habis.

---

## 8. Business Logic: Kalkulasi Denda (Logika Inti)
Algoritma denda diimplementasikan di level SQL melalui fungsi `fn_calculate_fine`:
```sql
CREATE FUNCTION fn_calculate_fine(due_date, return_date, fine_per_day)
BEGIN
    DECLARE late_days INT;
    SET late_days = DATEDIFF(return_date, due_date);
    IF late_days > 0 THEN
        RETURN late_days * fine_per_day;
    ELSE
        RETURN 0;
    END IF;
END;
```
Nilai `fine_per_day` diambil dari pengaturan variabel lingkungan (`.env`) atau default sistem (Rp 5.000).

---

## 9. Integrasi Frontend (Panduan untuk Developer UI)
API ini dirancang untuk mudah dikonsumsi oleh React, Vue, atau Mobile App:
*   **Header**: Selalu kirim `Authorization: Bearer <token>` untuk endpoint yang dikunci.
*   **Error Handling**: Sistem mengembalikan kode status HTTP yang standar (400 untuk input salah, 401 untuk token habis, 403 untuk dilarang akses, 404 untuk data tidak ada, 500 untuk error server).
*   **Format JSON**: Response sukses selalu dibungkus dalam objek:
    ```json
    {
        "success": true,
        "message": "...",
        "data": { ... }
    }
    ```

---

## 10. Panduan Deployment & Instalasi
1.  Clone repository.
2.  Buat virtual environment: `python -m venv venv`.
3.  Install dependencies: `pip install -r requirements.txt`.
4.  Konfigurasi `.env` (Database, Secret Key).
5.  Jalankan migrasi awal: `python manage.py migrate`.
6.  Import SQL manual: `mysql < stored_procedures.sql` dan `mysql < triggers.sql`.
7.  Jalankan server: `python manage.py runserver`.

---
**Dibuat oleh:** fathir

**Status:** Produksi / Siap Pakai
**Catatan Akhir:** Seluruh kode telah mengikuti standar PEP 8 (Python) dan normalisasi database tingkat ketiga (3NF).
