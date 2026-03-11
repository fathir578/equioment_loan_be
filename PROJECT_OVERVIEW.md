# 🏗️ Laporan Arsitektur & Implementasi Sistem: Backend Peminjaman Alat
**Dokumen Referensi Teknis Komprehensif — UKK RPL 2025/2026**

---

## 1. 📂 Pendahuluan
Sistem Peminjaman Alat ini dirancang sebagai platform backend yang tangguh, aman, dan efisien untuk manajemen inventaris di sekolah. Fokus utama proyek ini adalah menjaga **Integritas Data** melalui logika tingkat rendah di database (SQL) dan memberikan **Keamanan Berlapis** di tingkat aplikasi (Python/Django). Sistem ini tidak hanya mencatat data, tetapi juga memvalidasi setiap aturan bisnis secara otomatis untuk mencegah kesalahan manusia (*human error*).

---

## 2. 🏛️ Arsitektur Proyek: Modular Monolith
Aplikasi ini dibangun menggunakan arsitektur **Modular Monolith**. Meskipun berada dalam satu basis kode, setiap fungsi bisnis dipisahkan menjadi modul (app) mandiri di dalam folder `apps/`. Pendekatan ini memudahkan pemeliharaan, pengujian, dan potensi migrasi ke arsitektur microservices di masa depan.

### 2.1 Komponen Utama Direktori
*   **`config/`**: Pusat kendali global Django. Berisi pengaturan keamanan, koneksi database, konfigurasi JWT, dan routing utama (`urls.py`).
*   **`core/`**: Berisi logika inti yang bersifat lintas-modul (*cross-cutting concerns*), seperti:
    *   `middleware.py`: Audit trail otomatis.
    *   `permissions.py`: Implementasi RBAC (Role-Based Access Control).
    *   `exceptions.py`: Standardisasi error handling API.
    *   `utils.py`: Helper untuk QR Code (UUID4) dan kalkulasi denda.
*   **`apps/`**: Domain bisnis spesifik:
    *   `users`: Manajemen identitas, peran, dan otentikasi.
    *   `tools`: Katalog alat, stok, dan kondisi fisik.
    *   `categories`: Pengelompokan alat sekolah.
    *   `loans`: Transaksi peminjaman (Pusat logika bisnis).
    *   `returns`: Transaksi pengembalian dan manajemen denda.
    *   `activity_logs`: Rekam jejak audit digital.
*   **`sql/`**: Logika bisnis tingkat rendah (Triggers, Stored Procedures, Schema).

---

## 3. 🛡️ Keamanan Sistem Berlapis (v1.1.0+)
Keamanan adalah prioritas utama dalam sistem ini. Kami mengimplementasikan standar industri terbaru untuk melindungi data sensitif pengguna dan mencegah serangan siber.

### 🔐 3.1 Otentikasi & Autorisasi (RBAC)
*   **JWT (JSON Web Token)**: Digunakan untuk sesi stateless. Token akses memiliki umur singkat (1 jam), sementara *refresh token* digunakan untuk memperbarui sesi tanpa login ulang.
*   **Token Blacklisting**: Saat user logout, *refresh token* akan dimasukkan ke dalam daftar hitam (*blacklist*) di database, sehingga token tersebut tidak dapat digunakan lagi oleh penyusup.
*   **Role-Based Access Control (RBAC)**:
    *   **Admin**: Akses penuh ke seluruh sistem, laporan, dan manajemen user.
    *   **Petugas**: Mengelola inventaris, menyetujui peminjaman, dan memproses pengembalian.
    *   **Peminjam (Siswa)**: Hanya bisa mengajukan pinjaman dan melihat riwayat pribadinya.

### 🛡️ 3.2 Proteksi Data & Password
*   **Argon2 Hashing**: Menggunakan pemenang *Password Hashing Competition* sebagai algoritma utama. Argon2 jauh lebih kuat melawan serangan brute-force dan GPU dibandingkan MD5, SHA256, atau PBKDF2 standar.
*   **Security Headers**: 
    *   **HSTS (HTTP Strict Transport Security)**: Memaksa koneksi selalu menggunakan HTTPS.
    *   **XSS Filter**: Mencegah serangan *Cross-Site Scripting*.
    *   **Content-Type Nosniff**: Mencegah browser menebak tipe konten secara berbahaya.
    *   **X-Frame-Options**: Mencegah serangan *Clickjacking*.

### 🚦 3.3 Rate Limiting / Throttling
Mencegah penyalahgunaan API dan serangan DDoS tingkat aplikasi:
*   **Endpoint Login**: Dibatasi maksimal 5 percobaan per menit (Anti-Brute Force).
*   **Endpoint Publik/Umum**: Dibatasi 20 request/menit untuk user anonim.
*   **User Terautentikasi**: Dibatasi 100 request/menit untuk menjaga performa server.

---

## 4. 📝 Audit Trail & Logging Otomatis
Setiap aksi yang bersifat mengubah data (POST, PUT, PATCH, DELETE) akan dicatat secara otomatis oleh sistem tanpa perlu intervensi developer di setiap fungsi.

### 4.1 Detail Data Audit:
*   **User**: Siapa yang melakukan aksi.
*   **Action**: Endpoint dan metode HTTP yang diakses.
*   **IP Address**: Alamat jaringan pelaku (mendukung deteksi dari proxy/load balancer).
*   **User-Agent**: Informasi mengenai browser dan perangkat yang digunakan.
*   **Timestamp**: Waktu kejadian secara presisi hingga milidetik.

Log ini disimpan dengan relasi `ON DELETE SET NULL`, memastikan bahwa jika akun user dihapus, catatan riwayat aktivitasnya tetap tersimpan sebagai bukti audit yang sah.

---

## 5. 📱 Identitas Unik & QR Code (Safe Identifiers)
Sistem menggunakan **QR Code** untuk mempermudah identifikasi fisik alat dan kartu anggota siswa.

*   **Non-Predictable IDs**: Token QR di-generate menggunakan **UUID4** (Universally Unique Identifier). Berbeda dengan ID numerik (1, 2, 3), UUID tidak dapat ditebak oleh pihak luar, sehingga mencegah akses data secara acak (*ID Enumeration Attack*).
*   **Real-time Generation**: File gambar `.png` dibuat secara otomatis pada saat objek disimpan ke database menggunakan sinyal override `save()`.

---

## 6. ⚙️ Logika Bisnis Sisi Database (Performance & Integrity)
Berbeda dengan aplikasi standar, sistem ini memindahkan logika krusial ke dalam database (Stored Procedures & Triggers) untuk menjamin kecepatan dan konsistensi data.

### 6.1 Stored Procedures (`sql/stored_procedures.sql`)
*   **`sp_create_loan`**: Digunakan saat siswa mengajukan pinjaman. Prosedur ini menggunakan `START TRANSACTION` dan `FOR UPDATE` (Row Locking) untuk memastikan tidak ada dua orang yang bisa meminjam alat yang sama di detik yang sama jika stok hanya tersisa satu.
*   **`sp_process_return`**: Menghitung denda secara otomatis di sisi server. Jika terlambat, sistem akan langsung mengalikan selisih hari dengan tarif denda yang berlaku tanpa perlu bantuan kode Python.

### 6.2 Database Triggers (`sql/triggers.sql`)
*   **Auto-Stock Update**: Saat petugas mengubah status peminjaman menjadi 'Approved', trigger akan secara otomatis mengurangi stok di tabel `tools`. Begitu juga sebaliknya saat alat dikembalikan.
*   **Condition Downgrade Protection**: Jika alat dikembalikan dengan kondisi 'Rusak', trigger akan mengupdate kondisi permanen alat tersebut di katalog pusat agar tidak bisa dipinjam oleh orang lain sebelum diperbaiki.

---

## 7. 🧪 Strategi Pengujian & Validasi
Kualitas kode dijamin melalui pengujian otomatis yang mencakup:
*   **Integrity Testing**: Memastikan trigger database bekerja dengan benar saat ada perubahan status.
*   **Concurrency Testing**: Menguji keamanan transaksi saat banyak orang melakukan peminjaman secara bersamaan.
*   **Security Testing**: Memastikan endpoint yang diproteksi tidak bisa diakses tanpa token JWT yang valid.

---

## 8. 📊 Format API & Standarisasi Response
Untuk memudahkan integrasi dengan frontend (React/Angular), seluruh API mengikuti format seragam:
```json
{
    "success": true,
    "message": "Pesan keberhasilan dalam bahasa yang user-friendly",
    "data": { ... payload data ... }
}
```
Standardisasi ini mencakup penanganan error (Exception Handler) yang menyembunyikan detail teknis (*stack trace*) dari pengguna untuk alasan keamanan.

---

## 9. 🏁 Kesimpulan
Sistem Backend Peminjaman Alat (v1.1.x) bukan sekadar aplikasi CRUD biasa. Ini adalah sistem inventaris yang dirancang dengan standar keamanan tinggi dan integritas data yang sangat ketat. Dengan kombinasi Django REST Framework dan SQL Advanced (Stored Procedures/Triggers), sistem ini siap digunakan untuk skala produksi dengan performa yang optimal.

**Status Dokumentasi:** v1.1.2 (Final Update)
**Tanggal Diperbarui:** 11 Maret 2026
