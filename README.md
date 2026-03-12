# Equipment Loan System Backend
**School Equipment Loan Management System — UKK RPL 2025/2026**

[![Django](https://img.shields.io/badge/Django-4.2.10-092e20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14.0-ff1709?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![JWT](https://img.shields.io/badge/Authentication-JWT-000000?style=for-the-badge&logo=json-web-tokens&logoColor=white)](https://jwt.io/)
[![Version](https://img.shields.io/badge/Version-1.2.3--Stable-blue?style=for-the-badge)](https://github.com/fathir578/equioment_loan_be)

A production-ready REST API backend designed with high security standards for managing school equipment inventory. Built with low-level database business logic (Stored Procedures & Triggers) and multi-layer protection against common attack vectors.

---

## Key Features & Security

- **Argon2 Authentication & JWT**: Uses the **Argon2** algorithm (Password Hashing Competition winner) combined with a **Refresh Token Blacklist** system for highly secure sessions.
- **Multi-Layer Security**:
  - **Anti-Privilege Escalation**: Automatic protection on registration to prevent unauthorized users from gaining Admin access.
  - **Email Domain Validation**: Registration is restricted to verified school email domains only.
  - **Fine Manipulation Guard**: Fine calculation is locked server-side to prevent client-side data manipulation.
  - **Security Headers**: Equipped with HSTS, XSS Filter, Content-Type Options, and Referrer Policy.
  - **Rate Limiting**: Brute-force protection on critical endpoints (Login: 5 req/minute).
- **Dashboard Analytics**: Real-time statistics for inventory, users, and fines — accessible by Admin only.
- **Real-time QR Code**: Automatic generation of physical QR Code files (.png) based on secure **UUID4** (non-predictable).
- **SQL Logic Center**: Atomic transactions via Stored Procedures and automatic stock updates via Database Triggers.
- **Audit Trail**: Automatic activity logging that captures IP Address and User-Agent for every critical action.

---

## Installation Guide

### 1. Prerequisites
- Python 3.13+
- MariaDB / MySQL
- Git

### 2. Clone & Setup
```bash
git clone https://github.com/fathir578/equioment_loan_be.git
cd equioment_loan_be

# Create & Activate Virtual Environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install Dependencies (including argon2-cffi)
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and fill in your database credentials.

### 4. Database Setup
This system uses a combination of Django Migrations and Manual SQL Logic:
```bash
# 1. Run Django Migrations (Tables & Schema)
python manage.py migrate

# 2. Import Database Logic (Procedures & Triggers)
mysql -u root -p db_peminjaman_alat < sql/stored_procedures.sql
mysql -u root -p db_peminjaman_alat < sql/triggers.sql

# 3. Seed Initial Data (Optional - for Testing)
mysql -u root -p db_peminjaman_alat < sql/seed.sql
```

---

## Testing & Validation
Run the following commands to verify system integrity:
```bash
# Run Python Logic Tests
python manage.py test tests/

# Access API Documentation (Swagger UI)
# Server running at: http://localhost:8000/api/docs/
```

---

## Technical Documentation
- [**PROJECT_OVERVIEW.md**](./PROJECT_OVERVIEW.md) — Architecture & Security Details.
- [**DATABASE_ERD_EXPLAINED.md**](./DATABASE_ERD_EXPLAINED.md) — Schema & Database Relation Explanation.
- [**API_DOCUMENTATION.md**](./API_DOCUMENTATION.md) — Endpoint List & Usage Guide.

---

**Status:** Major Milestone v1.2.3 (Security Audited & Production Ready)  
**Release Date:** 12 March 2026
