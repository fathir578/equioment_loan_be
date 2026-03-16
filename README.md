# Equipment Loan System Backend
**School Equipment Loan Management System — UKK RPL 2025/2026**

[![Django](https://img.shields.io/badge/Django-4.2.10-092e20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.14.0-ff1709?style=for-the-badge&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![JWT](https://img.shields.io/badge/Authentication-JWT-000000?style=for-the-badge&logo=json-web-tokens&logoColor=white)](https://jwt.io/)
[![Version](https://img.shields.io/badge/Version-2.0.0--Stable-blue?style=for-the-badge)](https://github.com/fathir578/equioment_loan_be)

A production-ready REST API backend designed with high security standards for managing school equipment inventory. Built with low-level database business logic (Stored Procedures & Triggers) and multi-layer protection against common attack vectors.

---

## What's New in v2.0.0?

- **Departmental System**: Integrated 16 departments of SMKN 2 Subang for organized inventory and user management.
- **Student Identity**: Students now have full academic identity (NIS, Class, Department).
- **Automated Student Onboarding**: Staff can register students without email; passwords and QR cards are auto-generated.
- **Departmental Reports**: Professional Excel report generation per department, categorized by grade level (X, XI, XII).
- **Granular Permissions**: New `IsSameDepartment` permission ensures staff can only manage tools and students within their own department.
- **Improved QR Storage**: QR codes are now physically organized by department and class.

---

## Key Features & Security

- **Argon2 Authentication & JWT**: Uses the **Argon2** algorithm combined with a **Refresh Token Blacklist** system.
- **Multi-Layer Security**:
  - **Anti-Privilege Escalation**: Automatic protection on registration.
  - **Identity Validation**: Staff must use school domain email; students use NIS.
  - **Fine Manipulation Guard**: Fine calculation is locked server-side.
  - **Rate Limiting**: Brute-force protection (Login: 5 req/minute).
- **Dashboard & Reporting**: Real-time stats and downloadable Excel reports.
- **Real-time QR Code**: Automatic generation of physical QR Code files organized by department.
- **SQL Logic Center**: Atomic transactions via Stored Procedures and Triggers.
- **Audit Trail**: Activity logging captures IP, User-Agent, and detailed actions.

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

# Install Dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and fill in your database credentials.

### 4. Database Setup
```bash
# 1. Run Django Migrations
python manage.py migrate

# 2. Import Database Logic (Procedures & Triggers)
mysql -u root -p db_peminjaman_alat < sql/stored_procedures.sql
mysql -u root -p db_peminjaman_alat < sql/triggers.sql

# 3. Seed Initial Data
mysql -u root -p db_peminjaman_alat < sql/seed_departments.sql
mysql -u root -p db_peminjaman_alat < sql/seed.sql
```

---

## Testing & Validation
```bash
# Run All Tests
python manage.py test

# Access API Documentation (Swagger UI)
# Server running at: http://localhost:8000/api/docs/
```

---

## Technical Documentation
- [**PROJECT_OVERVIEW.md**](./PROJECT_OVERVIEW.md) — Architecture & Security Details.
- [**DATABASE_ERD_EXPLAINED.md**](./DATABASE_ERD_EXPLAINED.md) — Schema & Database Relation Explanation.
- [**API_DOCUMENTATION.md**](./API_DOCUMENTATION.md) — Endpoint List & Usage Guide.

---

**Status:** Major Milestone v2.0.0 (Departmental Release)  
**Release Date:** 16 March 2026
