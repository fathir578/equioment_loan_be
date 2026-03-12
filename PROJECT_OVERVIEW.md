# System Architecture & Implementation Report: Equipment Loan Backend
**Comprehensive Technical Reference Document — UKK RPL 2025/2026**

---

## 1. Introduction
This system is designed as a robust backend solution for managing equipment loans in a school environment. The primary focus of development is on **Data Integrity** (using database-side logic) and **Security** (using industry standards such as JWT, Argon2, and Rate Limiting). This document serves as a technical roadmap for understanding all system components.

---

## 2. Project Structure & Coding Guidelines
This project follows a **Modular Monolith** architecture pattern organized under the `apps/` folder. This separation ensures the code is readable, testable, and maintainable for future development.

### 2.1 Main Directories
- `config/`: Contains global Django configuration.
  - `settings.py`: Core configuration (Database, JWT, Middleware, Throttling, Security Headers).
  - `urls.py`: Main routing connecting all API modules.
  - `wsgi.py` & `asgi.py`: Entry points for production servers.
- `core/`: Contains shared logic used across all applications.
  - `permissions.py`: RBAC access control definitions (Admin, Petugas, Peminjam).
  - `pagination.py`: Standardized paginated response format.
  - `middleware.py`: Automatic activity logging middleware (Audit Trail).
  - `utils.py`: Helper functions (QR Code generator, response formatters).
  - `exceptions.py`: Global error handler ensuring all responses are JSON.
- `apps/`: Contains independent business modules.
  - `users/`: Authentication, registration, and profile management.
  - `categories/`: Equipment type classification.
  - `tools/`: Equipment inventory catalog.
  - `loans/`: Loan transactions and approval workflow.
  - `returns/`: Return transactions and fine calculation.
  - `activity_logs/`: System audit records.

---

## 3. Technical Criteria Implementation

### 3.1 Authentication & Authorization
The system uses **JSON Web Token (JWT)** for stateless authentication.
- **Login Implementation:** `apps/users/views.py` → `MyTokenObtainPairView`.
- **Custom Claims:** `role` and `username` are embedded into the token payload via `apps/users/serializers.py` → `MyTokenObtainPairSerializer`. This allows the frontend to read the user's role directly from the token without an extra API call.
- **Authorization (RBAC):** Access permissions are defined in `core/permissions.py`.
  - `IsAdminOrPetugas` — used on `/tools/` so only staff can modify equipment data.
  - `IsOwnerOrAdmin` — used on `/loans/` so students can only view their own data, while Admin can view all.
  - `IsPeminjam` — restricts loan creation to students only.

### 3.2 Rate Limiting / Throttling
Prevents brute-force attacks and API abuse.
- **Location:** `config/settings.py` under `REST_FRAMEWORK`.
- **Rules:**
  - `anon`: 20 requests/minute for unauthenticated users.
  - `user`: 100 requests/minute for authenticated users.
  - `login`: 5 requests/minute specifically for the `/auth/login/` endpoint.

### 3.3 Pagination
Ensures application performance remains fast even with thousands of records.
- **Location:** `core/pagination.py` → `StandardPagination` class.
- **Format:** Returns metadata including `total_pages`, `current_page`, `has_next`, `has_prev`, and `results`.
- **Default:** 10 items per page, adjustable via `?page_size=` query parameter.

### 3.4 Input Validation (Triple Layer)
Validation is applied at three layers:
1. **Serializer Layer:** Data type and format validation in `apps/*/serializers.py`. Includes email domain restriction — only `@smk-2sbg.sch.id` addresses are accepted during registration.
2. **Model Layer:** Business logic validation in `apps/loans/models.py` via the `clean()` method — ensures `due_date` cannot precede `loan_date`, and a borrower cannot approve their own loan.
3. **Database Layer:** CHECK constraints and Triggers in SQL — ensures stock never goes negative and approval rules are enforced even at the database level.

---

## 4. Database Architecture & SQL Logic

The system delegates heavy business logic to the database layer to guarantee absolute data consistency.

### 4.1 Main Tables & Relations
1. **`users`**: PK `id`, `username`, `email` (domain-restricted), `password` (Argon2 hash), `role`, `qr_token` (UUID4).
2. **`categories`**: PK `id`, `name`.
3. **`tools`**: PK `id`, FK `category_id`, `name`, `stock_total`, `stock_available`, `condition`, `qr_code` (UUID4).
4. **`loans`**: PK `id`, FK `user_id`, FK `approved_by`, `loan_date`, `due_date`, `status`.
5. **`loan_items`**: PK `id`, FK `loan_id`, FK `tool_id`, `quantity`, `quantity_returned`.
6. **`returns`**: PK `id`, FK `loan_id`, FK `processed_by`, `return_date`, `late_days`, `total_fine`.
7. **`return_items`**: PK `id`, FK `return_id`, FK `loan_item_id`, `quantity_returned`, `condition_on_return`.
8. **`activity_logs`**: PK `id`, FK `user_id`, `action`, `description`, `ip_address`.

### 4.2 Stored Procedures (`sql/stored_procedures.sql`)
- **`sp_create_loan`**:
  - Accepts user data, dates, and a JSON array of equipment items.
  - Algorithm:
    1. Validate input before opening a transaction.
    2. Start Transaction.
    3. Insert into `loans`.
    4. Loop through JSON items.
    5. Lock each tool row using `SELECT FOR UPDATE` (prevents race conditions).
    6. Check stock availability. If insufficient, `ROLLBACK` everything.
    7. If all checks pass, insert into `loan_items` and `COMMIT`.
- **`sp_process_return`**:
  - Supports partial returns — a loan can be returned across multiple sessions.
  - Automatically calculates fines using `fn_calculate_fine`.
  - Inserts into `return_items` per equipment, triggering automatic side effects.
- **`sp_get_user_by_qr`** & **`sp_get_tool_by_qr`**: QR code scan lookup procedures for the physical loan workflow.

### 4.3 Triggers (`sql/triggers.sql`)
- **`trg_validate_loan_approver`**: Validates that the approver has the correct role (`petugas` or `admin`) and cannot approve their own loan.
- **`trg_decrease_stock_on_approve`**: When loan status changes to `approved`, stock in `tools` is automatically reduced using cursor with `FOR UPDATE` locking.
- **`trg_restore_stock_on_reject`**: If a previously approved loan is rejected, stock is restored automatically.
- **`trg_process_return_item`**: On each return item insert — updates `quantity_returned`, restores stock, applies downgrade-only condition rule, and automatically updates loan status to `partial_returned` or `returned`.
- **`trg_check_stock_before_loan_item`**: Pre-validation guard before inserting into `loan_items`.
- **`trg_log_new_user`**: Automatically logs to `activity_logs` whenever a new user is created.

---

## 5. System Workflows

### 5.1 Loan Cycle
1. **Register/Login**: User receives a JWT access token.
2. **Submit Request**: User calls `POST /api/v1/loans/`. Logic is executed by `sp_create_loan`. Status: `pending`.
3. **Verification**: Staff physically verifies equipment availability.
4. **Approval**: Staff calls `POST /api/v1/loans/{id}/approve/`. Database trigger automatically reduces stock. Status: `approved`.

### 5.2 Return Cycle
1. **Equipment Return**: Student brings equipment back to staff.
2. **Data Input**: Staff calls `POST /api/v1/returns/` with a list of returned items and their conditions.
3. **Calculation**: Database calculates late days. If `late_days > 0`, fine is calculated automatically.
4. **Auto Update**: Stock increases automatically via trigger. Loan status updates to `partial_returned` or `returned` depending on whether all items have been returned.

---

## 6. Audit Trail & Activity Logging

The system records every user action for security and accountability:
- **Middleware Log**: `core/middleware.py` captures every `POST`, `PUT`, `PATCH`, and `DELETE` request. Recorded information includes: User ID, endpoint URL, HTTP method, IP Address, and Timestamp.
- **Database Log**: The `trg_log_new_user` trigger records directly to `activity_logs` on every new user creation.
- **Monitoring**: Admin can monitor all logs via `GET /api/v1/logs/`.

---

## 7. Security & Encryption

- **Password Hashing**: Uses **Argon2** (Password Hashing Competition 2015 winner) as the primary hasher. Passwords are never stored in plain text. Each hash uses a unique salt generated at the time of hashing.
- **Email Domain Restriction**: Registration is restricted to verified school email domains (`@smk-2sbg.sch.id`). Requests with unauthorized domains are rejected at the serializer layer.
- **JWT Security**: Tokens have an expiration time (Access: 60 minutes, Refresh: 7 days). `ROTATE_REFRESH_TOKENS` and `BLACKLIST_AFTER_ROTATION` are enabled — used refresh tokens are immediately invalidated to prevent replay attacks.
- **Security Headers**: HSTS, XSS Filter, Content-Type Options, X-Frame-Options (DENY), and Referrer Policy are configured in `settings.py`.
- **CORS Policy**: Only specific frontend origins are allowed to access the API.

---

## 8. Business Logic: Fine Calculation
The fine calculation algorithm is implemented at the SQL level via `fn_calculate_fine`:

```sql
CREATE FUNCTION fn_calculate_fine(due_date, return_date, fine_per_day)
BEGIN
    DECLARE late_days INT;
    SET late_days = DATEDIFF(return_date, due_date);
    IF late_days > 0 THEN
        RETURN late_days * fine_per_day;
    ELSE
        RETURN 0;
    END IF;
END;
```

The `fine_per_day` value is taken from the environment variable (`DEFAULT_FINE_PER_DAY`) with a system default of Rp 5,000 per day.

---

## 9. Frontend Integration Guide
This API is designed to be easily consumed by React, Vue, or Mobile applications:
- **Header**: Always send `Authorization: Bearer <token>` for protected endpoints.
- **Error Handling**: The system returns standard HTTP status codes (400 for bad input, 401 for expired token, 403 for forbidden access, 404 for not found, 500 for server error).
- **JSON Format**: All responses are wrapped in a consistent structure:
  ```json
  {
      "success": true,
      "message": "...",
      "data": { ... }
  }
  ```

---

## 10. Deployment & Installation Guide
1. Clone the repository.
2. Create a virtual environment: `python -m venv venv`.
3. Install dependencies: `pip install -r requirements.txt`.
4. Configure `.env` (Database credentials, Secret Key, Fine settings).
5. Run Django migrations: `python manage.py migrate`.
6. Import SQL logic via MySQL shell:
   ```sql
   SOURCE sql/stored_procedures.sql;
   SOURCE sql/triggers.sql;
   SOURCE sql/seed.sql;
   ```
7. Create initial users via Django shell: `python manage.py shell`.
8. Run the development server: `python manage.py runserver`.

---

**Author:** fathir578  
**Status:** Production Ready — v1.2.3  
**Notes:** All code follows PEP 8 standards (Python) and third normal form database normalization (3NF).
