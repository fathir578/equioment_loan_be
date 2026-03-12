# Database ERD — Equipment Loan System
**Version:** v1.2.3

```mermaid
erDiagram
    users {
        int id PK
        varchar username UK
        varchar email UK
        varchar password
        enum role
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
        datetime created_at
    }

    %% Relasi
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

---

## Keterangan Relasi

| Relasi | Tipe | Keterangan |
|--------|------|------------|
| `users` → `loans` (user_id) | One to Many | Satu user bisa punya banyak pinjaman |
| `users` → `loans` (approved_by) | One to Many | Satu petugas bisa approve banyak pinjaman |
| `users` → `returns` | One to Many | Satu petugas bisa proses banyak pengembalian |
| `categories` → `tools` | One to Many | Satu kategori bisa punya banyak alat |
| `loans` → `loan_items` | One to Many | Satu pinjaman bisa punya banyak alat |
| `loans` → `returns` | One to Many | Satu pinjaman bisa punya banyak sesi pengembalian |
| `returns` → `return_items` | One to Many | Satu sesi pengembalian bisa punya banyak alat |
| `loan_items` → `return_items` | One to Many | Satu loan item bisa dikembalikan bertahap |

---

## Catatan Penting

- `loans.approved_by` **nullable** — kosong saat pertama dibuat, diisi saat disetujui
- `returns.loan_id` **tidak UNIQUE** — satu loan bisa punya banyak sesi pengembalian (partial return)
- `loan_items.quantity_returned` — diupdate otomatis oleh trigger `trg_process_return_item`
- `tools.condition` — hanya bisa turun (downgrade-only), tidak pernah naik otomatis
