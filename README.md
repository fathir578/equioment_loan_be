# 🛠️ Equipment Loan System Backend
**Sistem Manajemen Peminjaman Alat Sekolah — UKK RPL 2025/2026**

[![Django](https://img.shields.io/badge/Django-4.2.10-092e20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14.0-ff1709?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![JWT](https://img.shields.io/badge/Authentication-JWT-000000?style=for-the-badge&logo=json-web-tokens&logoColor=white)](https://jwt.io/)

Sistem backend ini menyediakan solusi API yang aman, cepat, dan terpercaya untuk mengelola peminjaman serta inventaris alat sekolah. Dilengkapi dengan logika bisnis tingkat tinggi yang ditanam langsung pada database (Stored Procedures & Triggers).

---

## ✨ Fitur Utama
Sistem ini telah mengimplementasikan seluruh kriteria teknis wajib dan fitur tambahan profesional:

*   **🔐 Autentikasi & RBAC**: Login menggunakan JWT dengan hak akses bertingkat (Admin, Petugas, Peminjam).
*   **📊 Dashboard Analytics**: Endpoint khusus untuk statistik data inventaris dan keuangan secara real-time.
*   **📱 Real-time QR Code**: Otomatisasi pembuatan file fisik QR Code (.png) saat registrasi user atau penambahan alat baru.
*   **📁 Export Laporan**: Fitur unduh laporan peminjaman lengkap dalam format CSV yang kompatibel dengan Excel.
*   **💰 Smart Fine Calculation**: Perhitungan denda otomatis melalui Stored Procedure database berdasarkan keterlambatan pengembalian.
*   **🛡️ Integrity Protection**: Validasi stok dan approval yang aman menggunakan Database Triggers (Safety Net).
*   **📝 Audit Trail**: Pencatatan log aktivitas user secara otomatis untuk setiap aksi krusial.
*   **🧪 Automated Testing**: Skrip pengujian otomatis untuk menjamin validitas logika bisnis.

---

## 🚀 Panduan Instalasi & Penggunaan

### 1. Prasyarat
*   Python 3.13+
*   MariaDB / MySQL
*   Git

### 2. Kloning Repositori
```bash
git clone https://github.com/fathir578/equioment_loan_be.git
cd equioment_loan_be
```

### 3. Setup Lingkungan
```bash
# Buat virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependensi
pip install -r requirements.txt
```

### 4. Konfigurasi Database
Salin file `.env.example` menjadi `.env` dan isi kredensial database Anda:
```env
DB_NAME=db_peminjaman_alat
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306
```

### 5. Migrasi & SQL Manual
```bash
# Jalankan migrasi Django
python manage.py migrate

# Jalankan skrip perbaikan default (opsional jika manual)
# python manage.py shell < fix_db_defaults.py (jika file tersedia)

# Import Stored Procedures & Triggers
mysql -u root -p db_peminjaman_alat < stored_procedures.sql
mysql -u root -p db_peminjaman_alat < triggers.sql
```

### 6. Jalankan Server
```bash
python manage.py runserver
```
Akses Dokumentasi API di: [http://localhost:8000/api/docs/](http://localhost:8000/api/docs/)

---

## 📖 Dokumentasi Lengkap
Untuk detail teknis mengenai arsitektur, skema database, dan alur kerja sistem, silakan baca:
👉 [**PROJECT_OVERVIEW.md**](./PROJECT_OVERVIEW.md)

Untuk daftar lengkap endpoint API, silakan baca:
👉 [**API_DOCUMENTATION.md**](./API_DOCUMENTATION.md)

---

## 🧪 Pengujian Otomatis
Jalankan perintah berikut untuk memverifikasi logika bisnis (stok & denda):
```bash
python manage.py test tests/
```

---
**Status Proyek:** Produksi / Siap Digunakan (v1.0.0)
