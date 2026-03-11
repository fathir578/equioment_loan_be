# 🔧 Aplikasi Peminjaman Alat — API Backend

<<<<<<< Updated upstream
REST API untuk sistem peminjaman alat sekolah.
Dibangun dengan Django + DRF + MySQL.

---

## ⚙️ Setup Lokal (Dari Nol)

### 1. Clone & Masuk Folder
=======
[![Django](https://img.shields.io/badge/Django-4.2.10-092e20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14.0-ff1709?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![JWT](https://img.shields.io/badge/Authentication-JWT-000000?style=for-the-badge&logo=json-web-tokens&logoColor=white)](https://jwt.io/)

Sistem backend ini menyediakan solusi API yang aman, cepat, dan terpercaya untuk mengelola peminjaman serta inventaris alat sekolah. Dilengkapi dengan logika bisnis tingkat tinggi yang ditanam langsung pada database (Stored Procedures & Triggers) dan pengamanan ekstra tingkat lanjut.

---

## ✨ Fitur Utama & Keamanan
Sistem ini telah mengimplementasikan seluruh kriteria teknis wajib dan fitur tambahan profesional:

*   **🔐 Autentikasi & RBAC**: Login menggunakan JWT dengan sistem **Refresh Token** dan **Blacklist** saat logout.
*   **🛡️ Enhanced Security**: 
    *   **Password Hashing**: Menggunakan algoritma **Argon2** (pemenang Password Hashing Competition).
    *   **Security Headers**: Dilengkapi dengan HSTS, XSS Filter, Content-Type Options, dan Referrer Policy.
    *   **Rate Limiting**: Proteksi anti brute-force pada endpoint login (5 req/menit).
*   **📊 Dashboard Analytics**: Endpoint khusus untuk statistik data inventaris dan keuangan secara real-time.
*   **📱 Real-time QR Code**: Otomatisasi pembuatan file fisik QR Code (.png) menggunakan **UUID4** yang aman (non-predictable).
*   **📁 Export Laporan**: Fitur unduh laporan peminjaman lengkap dalam format CSV yang kompatibel dengan Excel.
*   **💰 Smart Fine Calculation**: Perhitungan denda otomatis melalui Stored Procedure database dengan kontrol transaksi yang ketat.
*   **📝 Audit Trail Pro**: Pencatatan log aktivitas user secara otomatis termasuk **IP Address** dan **User-Agent** untuk pelacakan anomali.
*   **🧪 Automated Testing**: Skrip pengujian otomatis untuk menjamin validitas logika bisnis.

---

## 🚀 Panduan Instalasi & Penggunaan

### 1. Prasyarat
*   Python 3.13+
*   MariaDB / MySQL
*   Git

### 2. Kloning Repositori
>>>>>>> Stashed changes
```bash
git clone <repo-url>
cd peminjaman-alat
```

### 2. Buat Virtual Environment
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

<<<<<<< Updated upstream
### 3. Install Dependencies
```bash
=======
# Install dependensi (termasuk argon2-cffi)
>>>>>>> Stashed changes
pip install -r requirements.txt
```

### 4. Setup Environment Variables
```bash
<<<<<<< Updated upstream
cp .env.example .env
# Edit .env sesuai konfigurasi lokal kamu (DB password, secret key, dll)
=======
# Jalankan migrasi Django
python manage.py migrate

# Import Stored Procedures & Triggers
mysql -u root -p db_peminjaman_alat < sql/stored_procedures.sql
mysql -u root -p db_peminjaman_alat < sql/triggers.sql
>>>>>>> Stashed changes
```

### 5. Buat Database di MySQL
```bash
mysql -u root -p
```
```sql
CREATE DATABASE db_peminjaman_alat CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
EXIT;
```

### 6. Jalankan SQL Files (urutan penting!)
```bash
mysql -u root -p db_peminjaman_alat < sql/schema.sql
mysql -u root -p db_peminjaman_alat < sql/triggers.sql
mysql -u root -p db_peminjaman_alat < sql/stored_procedures.sql
mysql -u root -p db_peminjaman_alat < sql/seed.sql
```

### 7. Jalankan Migrasi Django
```bash
python manage.py migrate
```

### 8. Jalankan Server
```bash
python manage.py runserver
```

### 9. Akses API Docs
Buka browser: http://localhost:8000/api/docs/

---

## 🌿 Git Workflow

```bash
# Mulai fitur baru
git checkout develop
git pull origin develop
git checkout -b feature/nama-fitur

# Setelah selesai
git checkout develop
git merge --no-ff feature/nama-fitur
git push origin develop
git branch -d feature/nama-fitur
```

## 🏷️ Versioning
```
v0.1.0  → Foundation (DB + struktur project)
v0.2.0  → Auth & User management
v0.3.0  → Tools & Categories
v0.4.0  → Loans
v0.5.0  → Returns & Denda
v0.6.0  → QR Code
v1.0.0  → Production ready
```

---
<<<<<<< Updated upstream

## 👥 Akun Default (Development)

| Username | Password | Role |
|---|---|---|
| admin | Password123! | Admin |
| petugas1 | Password123! | Petugas |
| budi | Password123! | Peminjam |
| sari | Password123! | Peminjam |

> ⚠️ Ganti semua password ini sebelum production!

---

## 📁 Struktur Folder

```
peminjaman-alat/
├── apps/               # Semua Django apps (modul)
│   ├── users/
│   ├── categories/
│   ├── tools/
│   ├── loans/
│   ├── returns/
│   └── activity_logs/
├── config/             # Settings & URL router
├── core/               # Shared: pagination, permissions, utils
├── sql/                # File SQL: schema, triggers, procedures
├── tests/              # Test cases
├── manage.py
├── requirements.txt
└── .env.example
```
=======
**Status Proyek:** Produksi / Siap Digunakan (v1.1.0)
>>>>>>> Stashed changes
