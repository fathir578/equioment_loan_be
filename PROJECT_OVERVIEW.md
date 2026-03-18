# System Architecture & Implementation Report: Equipment Loan Backend
**Comprehensive Technical Reference Document — UKK RPL 2025/2026**

---

## 1. Introduction
This system is designed as a robust backend solution for managing equipment loans in a school environment. The primary focus of development is on **Data Integrity** (using database-side logic) and **Security** (using industry standards such as JWT, Argon2, and Rate Limiting).

**Latest Version:** v2.0.0 (Sprint 1: Department & Student Identity, Sprint 2: Excel Reports)

---

## 2. Project Structure & Coding Guidelines
This project follows a **Modular Monolith** architecture pattern organized under the `apps/` folder.

### 2.1 Main Directories
- `config/`: Global Django configuration.
- `core/`: Shared logic (Permissions, Utils, Middleware, Pagination).
- `apps/`: Independent business modules.
  - `departments/`: [v2.0.0] School department management (16 departments).
  - `users/`: [v2.0.0 Updated] Authentication with Student Identity (NIS, Class).
  - `tools/`: [v2.0.0 Updated] Equipment catalog with Department ownership.
  - `reports/`: [v2.0.0] Excel report generation per department.
  - `categories/`, `loans/`, `returns/`, `activity_logs/`.

---

## 3. Technical Criteria Implementation (v2.0.0 Updates)

### 3.1 Authentication & Authorization
- **Student Identity:** Students (Peminjam) now have NIS, Full Name, Class, and Department.
- **Registration Flow:** Admin/Petugas can register students without email. Passwords are auto-generated.
- **New Permissions (RBAC):**
  - `CanRegisterPeminjam`: Only Admin/Petugas can register and verify students.
  - `IsSameDepartment`: Petugas are restricted to their own department's data (tools, students, loans).

### 3.2 QR Code System [v2.0.0]
QR codes are now organized by department and class for better physical management:
- **Users:** `media/qrcodes/users/{DEPT}/{CLASS}/qr_{NIS}.png`
- **Tools:** `media/qrcodes/tools/{DEPT}/qr_{TOOL_NAME}.png`

### 3.3 Reporting Engine [v2.0.0]
Generates professional Excel reports using `openpyxl`:
- **Path:** `media/reports/{DEPT}/laporan_{DEPT}_{YYYY_MM}.xlsx`
- **Features:** 
  - Summary sheet ("Semua Kelas").
  - Categorized sheets per grade level (X, XI, XII).
  - Automatic fine summation and status tracking.
  - Professional styling (Bold headers, blue background, auto-width).

---

## 4. Database Architecture (v2.0.0)

### 4.1 New & Updated Tables
1. **`departments`**: [NEW] PK `id`, `kode`, `nama`, `bidang`.
2. **`users`**: [UPDATED] Added `department_id` (FK), `nis`, `nama_lengkap`, `kelas`, `is_verified`. `email` is now optional for students.
3. **`tools`**: [UPDATED] Added `department_id` (FK) to track equipment ownership per department.

---

## 5. System Workflows (v2.0.0)

### 5.1 Student Registration & Verification
1. **Registration**: Staff registers student via `POST /api/v1/users/peminjam/` using NIS and Class.
2. **QR Generation**: System automatically generates a QR Card in the department-specific folder.
3. **Verification**: Staff verifies student account via `POST /api/v1/users/{id}/verify/` after checking physical ID.

### 5.2 Departmental Reporting
1. **Request**: Staff calls `GET /api/v1/reports/{dept_kode}/`.
2. **Generation**: System aggregates all loan data for that department.
3. **Delivery**: Staff receives a stylized Excel file for monthly reporting.

---

## 6. Audit Trail & Activity Logging
- Capture every `POST`, `PUT`, `PATCH`, and `DELETE` request.
- Logs include IP Address, User Agent, and specific action descriptions.

---

## 7. Security & Encryption
- **Argon2** password hashing.
- **JWT** with rotation and blacklisting.
- **Clean Validation**: Model-level validation for email domains (staff only) and student identity fields.

---

**Author:** fathir578  
**Status:** Production Ready — v2.0.0  
**Date:** March 16, 2026
