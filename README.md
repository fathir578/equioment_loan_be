# 🔧 Aplikasi Peminjaman Alat — API Backend

REST API untuk sistem peminjaman alat sekolah.
Dibangun dengan Django + DRF + MySQL.

---

## ⚙️ Setup Lokal (Dari Nol)

### 1. Clone & Masuk Folder
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

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables
```bash
cp .env.example .env
# Edit .env sesuai konfigurasi lokal kamu (DB password, secret key, dll)
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
