# 🛠️ Equipment Loan System Backend
**Sistem Manajemen Peminjaman Alat Sekolah — UKK RPL 2025/2026**

[![Django](https://img.shields.io/badge/Django-4.2.10-092e20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14.0-ff1709?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![JWT](https://img.shields.io/badge/Authentication-JWT-000000?style=for-the-badge&logo=json-web-tokens&logoColor=white)](https://jwt.io/)
[![Version](https://img.shields.io/badge/Version-1.2.0--Stable-blue?style=for-the-badge)](https://github.com/fathir578/equioment_loan_be)

Sistem backend ini adalah solusi API **Production-Ready** yang dirancang dengan standar keamanan tinggi untuk manajemen inventaris sekolah. Dilengkapi dengan logika bisnis tingkat rendah pada database (Stored Procedures & Triggers) dan proteksi berlapis terhadap serangan siber.

---

## ✨ Fitur Utama & Keamanan Mutakhir
Sistem ini telah melewati audit keamanan mendalam dan mengimplementasikan fitur profesional:

*   **🔐 Autentikasi Argon2 & JWT**: Menggunakan algoritma **Argon2** (pemenang Password Hashing Competition) dan sistem **Refresh Token Blacklist** untuk sesi yang sangat aman.
*   **🛡️ Keamanan Berlapis**:
    *   **Anti-Privilege Escalation**: Proteksi otomatis pada registrasi untuk mencegah pendaftar ilegal mendapatkan hak akses Admin.
    *   **Fine Manipulation Guard**: Kalkulasi denda dikunci di sisi server (backend) untuk mencegah manipulasi data oleh klien.
    *   **Security Headers**: Dilengkapi HSTS, XSS Filter, Content-Type Options, dan Referrer Policy.
    *   **Rate Limiting**: Proteksi anti brute-force pada endpoint krusial (Login: 5 req/menit).
*   **📊 Dashboard Analytics**: Statistik data inventaris, pengguna, dan denda secara real-time untuk Admin.
*   **📱 Real-time QR Code**: Otomatisasi generate fisik QR Code (.png) berbasis **UUID4** yang aman (non-predictable).
*   **💰 SQL Logic Center**: Transaksi atomik via Stored Procedures dan pembaruan stok otomatis via Database Triggers.
*   **📝 Audit Trail Pro**: Pencatatan log aktivitas otomatis yang mencakup IP Address dan User-Agent.

---

## 🚀 Panduan Instalasi

### 1. Prasyarat
*   Python 3.13+
*   MariaDB / MySQL
*   Git

### 2. Kloning & Setup
```bash
git clone https://github.com/fathir578/equioment_loan_be.git
cd equioment_loan_be

# Buat & Aktifkan Virtual Environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install Dependensi (Termasuk argon2-cffi)
pip install -r requirements.txt
```

### 3. Konfigurasi Lingkungan
Salin file `.env.example` menjadi `.env` dan isi kredensial database Anda.

### 4. Sinkronisasi Database
Sistem menggunakan kombinasi Django Migrations dan Manual SQL Logic:
```bash
# 1. Jalankan Migrasi Django (Tabel & Skema)
python manage.py migrate

# 2. Import Logic Database (Prosedur & Trigger)
mysql -u root -p db_peminjaman_alat < sql/stored_procedures.sql
mysql -u root -p db_peminjaman_alat < sql/triggers.sql

# 3. Seed Data Awal (Opsional - Testing)
mysql -u root -p db_peminjaman_alat < sql/seed.sql
```

---

## 🧪 Validasi & Pengujian
Jalankan perintah berikut untuk memverifikasi kesehatan sistem:
```bash
# Uji Logika Python
python manage.py test tests/

# Dokumentasi API (Swagger)
# Server Running di: http://localhost:8000/api/docs/
```

---

## 📖 Dokumentasi Teknis
*   [**PROJECT_OVERVIEW.md**](./PROJECT_OVERVIEW.md) — Arsitektur & Keamanan Detail.
*   [**DATABASE_ERD_EXPLAINED.md**](./DATABASE_ERD_EXPLAINED.md) — Penjelasan Skema & Relasi DB.
*   [**API_DOCUMENTATION.md**](./API_DOCUMENTATION.md) — Daftar Endpoint & Cara Pakai.

---
**Status:** Major Milestone v1.2.0 (Security Audited & Production Ready)
**Tanggal Rilis:** 11 Maret 2026
