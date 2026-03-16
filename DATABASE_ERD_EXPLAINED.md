# Database Structure & ERD Explanation
**Project:** School Equipment Loan Management System  
**Version:** v2.0.0 (Departmental Release)
**Status:** Technical Document (Developer Reference)

---

## 1. Entity Relationship Diagram

```mermaid
erDiagram
    departments {
        int id PK
        varchar kode UK
        varchar nama
        varchar bidang
        tinyint is_active
        datetime created_at
    }

    users {
        int id PK
        int department_id FK
        varchar username UK
        varchar email UK
        varchar password
        enum role
        varchar nis UK
        varchar nama_lengkap
        varchar kelas
        tinyint is_verified
        varchar qr_token UK
        tinyint is_active
        tinyint is_staff
        tinyint is_superuser
        datetime created_at
        datetime updated_at
    }

    categories {
        int id PK
        varchar name UK
        text description
        datetime created_at
    }

    tools {
        int id PK
        int category_id FK
        int department_id FK
        varchar name
        text description
        varchar qr_code UK
        int stock_total
        int stock_available
        enum condition
        tinyint is_active
        datetime created_at
        datetime updated_at
    }

    loans {
        int id PK
        int user_id FK
        int approved_by FK
        date loan_date
        date due_date
        enum status
        text notes
        datetime created_at
        datetime updated_at
    }

    loan_items {
        int id PK
        int loan_id FK
        int tool_id FK
        int quantity
        int quantity_returned
    }

    returns {
        int id PK
        int loan_id FK
        int processed_by FK
        date return_date
        int late_days
        decimal fine_per_day
        decimal total_fine
        text notes
        datetime created_at
    }

    return_items {
        int id PK
        int return_id FK
        int loan_item_id FK
        int quantity_returned
        enum condition_on_return
    }

    activity_logs {
        int id PK
        int user_id FK
        varchar action
        text description
        varchar ip_address
        text user_agent
        datetime created_at
    }

    departments ||--o{ users : "memiliki"
    departments ||--o{ tools : "memiliki"
    users ||--o{ loans : "meminjam (user_id)"
    users ||--o{ loans : "menyetujui (approved_by)"
    users ||--o{ returns : "memproses (processed_by)"
    users ||--o{ activity_logs : "melakukan"
    categories ||--o{ tools : "mengklasifikasi"
    tools ||--o{ loan_items : "dipinjam"
    loans ||--o{ loan_items : "berisi"
    loans ||--o{ returns : "dikembalikan"
    returns ||--o{ return_items : "berisi"
    loan_items ||--o{ return_items : "direferensikan"
```

### Relation Summary (v2.0.0 Updates)

| Relation | Type | Description |
|----------|------|-------------|
| `departments` → `users` | One to Many | One department has many students/staff |
| `departments` → `tools` | One to Many | One department owns many tools |
| `users` → `loans` (user_id) | One to Many | One student can have many loans |
| `users` → `loans` (approved_by) | One to Many | One staff can approve many loans |
| `categories` → `tools` | One to Many | One category can have many tools |

---

## 2. Table Details (v2.0.0 Updates)

### 2.1 Table `departments` [NEW v2.0.0]
Stores information about school departments (e.g., RPL, TPM, TSM).

| Column | Type | Description |
|--------|------|-------------|
| `id` | INT | Primary Key |
| `kode` | VARCHAR(10) | Unique code (e.g., 'RPL') |
| `nama` | VARCHAR(100) | Full name of the department |
| `bidang` | VARCHAR(100) | Industry field (e.g., 'Agribisnis') |

---

### 2.2 Table `users` [UPDATED v2.0.0]
Added departmental and academic identity fields.

| Column | Type | Description |
|--------|------|-------------|
| `department_id` | INT | Foreign Key to `departments` (nullable for generic admin) |
| `nis` | VARCHAR(20) | Unique Student Identification Number |
| `nama_lengkap` | VARCHAR(100) | Student's full name |
| `kelas` | VARCHAR(20) | Student's class (e.g., 'X RPL A') |
| `is_verified` | TINYINT | Verification flag for student identity |

---

### 2.3 Table `tools` [UPDATED v2.0.0]
Added departmental ownership.

| Column | Type | Description |
|--------|------|-------------|
| `department_id` | INT | Foreign Key to `departments` (nullable for general equipment) |

---

### 2.4 Table `activity_logs` [UPDATED v2.0.0]
Added user agent tracking for better audit trails.

| Column | Type | Description |
|--------|------|-------------|
| `user_agent` | TEXT | Captured browser/client signature |

---

## 3. SQL Logic Integration

The v2.0.0 system continues to use **Stored Procedures** and **Triggers** for core logic (fines, stock, audit logs) while adding departmental context for access control. Database triggers ensure that even if the API is bypassed, data integrity across departments is maintained.
