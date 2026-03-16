-- ============================================================
--  APLIKASI PEMINJAMAN ALAT — schema.sql
--  Versi 2.0.0 — Sprint 1: Department & Student Identity
-- ============================================================

CREATE DATABASE IF NOT EXISTS db_peminjaman_alat
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE db_peminjaman_alat;

-- ------------------------------------------------------------
-- 0. DEPARTMENTS [NEW v2.0.0]
-- ------------------------------------------------------------
CREATE TABLE departments (
    id         INT UNSIGNED NOT NULL AUTO_INCREMENT,
    kode       VARCHAR(10)  NOT NULL UNIQUE,
    nama       VARCHAR(100) NOT NULL,
    bidang     VARCHAR(100) NOT NULL,
    is_active  TINYINT      NOT NULL DEFAULT 1,
    created_at DATETIME     DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_dept_kode (kode)
) ENGINE=InnoDB;


-- ------------------------------------------------------------
-- 1. USERS [UPDATED v2.0.0]
-- ------------------------------------------------------------
CREATE TABLE users (
    id            INT UNSIGNED     NOT NULL AUTO_INCREMENT,
    username      VARCHAR(50)      NOT NULL UNIQUE,
    email         VARCHAR(100)     NULL UNIQUE,  -- [v2.0.0] Jadi NULL untuk Peminjam
    password_hash VARCHAR(255)     NOT NULL,
    role          ENUM('admin','petugas','peminjam') NOT NULL DEFAULT 'peminjam',
    
    -- [NEW v2.0.0] Identitas Siswa
    department_id INT UNSIGNED     NULL,
    nis           VARCHAR(20)      NULL UNIQUE,
    nama_lengkap  VARCHAR(100)     NULL,
    kelas         VARCHAR(20)      NULL,
    is_verified   TINYINT          NOT NULL DEFAULT 0,

    qr_token      VARCHAR(64)      NOT NULL UNIQUE
                  COMMENT 'Token unik yang di-encode jadi QR Card user',
    is_active     TINYINT(1)       NOT NULL DEFAULT 1,
    is_staff      TINYINT(1)       NOT NULL DEFAULT 0,
    is_superuser  TINYINT(1)       NOT NULL DEFAULT 0,
    created_at    DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP
                  ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_users_department
        FOREIGN KEY (department_id) REFERENCES departments(id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    INDEX idx_users_role (role),
    INDEX idx_users_qr_token (qr_token),
    INDEX idx_users_dept (department_id),
    INDEX idx_users_nis (nis)
) ENGINE=InnoDB;


-- ------------------------------------------------------------
-- 2. CATEGORIES
-- ------------------------------------------------------------
CREATE TABLE categories (
    id          INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    name        VARCHAR(100)  NOT NULL UNIQUE,
    description TEXT,
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
) ENGINE=InnoDB;


-- ------------------------------------------------------------
-- 3. TOOLS [UPDATED v2.0.0]
-- ------------------------------------------------------------
CREATE TABLE tools (
    id              INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    category_id     INT UNSIGNED  NOT NULL,
    department_id   INT UNSIGNED  NULL, -- [NEW v2.0.0] Kepemilikan per Jurusan
    name            VARCHAR(150)  NOT NULL,
    description     TEXT,
    qr_code         VARCHAR(64)   NOT NULL UNIQUE
                    COMMENT 'Token unik yang di-encode jadi label QR alat',
    stock_total     INT UNSIGNED  NOT NULL DEFAULT 1,
    stock_available INT UNSIGNED  NOT NULL DEFAULT 1,
    `condition`     ENUM('baik','rusak_ringan','rusak_berat') NOT NULL DEFAULT 'baik',
    is_active       TINYINT(1)    NOT NULL DEFAULT 1,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_tools_category
        FOREIGN KEY (category_id) REFERENCES categories(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_tools_department
        FOREIGN KEY (department_id) REFERENCES departments(id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_stock CHECK (stock_available <= stock_total),
    INDEX idx_tools_qr_code (qr_code),
    INDEX idx_tools_category (category_id),
    INDEX idx_tools_dept (department_id),
    INDEX idx_tools_is_active (is_active)
) ENGINE=InnoDB;


-- ------------------------------------------------------------
-- 4. LOANS
-- ------------------------------------------------------------
CREATE TABLE loans (
    id          INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    user_id     INT UNSIGNED  NOT NULL  COMMENT 'Peminjam',
    approved_by INT UNSIGNED  NULL      COMMENT 'Petugas/Admin yang approve',
    loan_date   DATE          NOT NULL,
    due_date    DATE          NOT NULL,
    status      ENUM(
                    'pending',
                    'approved',
                    'rejected',
                    'partial_returned',
                    'returned'
                ) NOT NULL DEFAULT 'pending',
    notes       TEXT,
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP
                ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_loans_user
        FOREIGN KEY (user_id) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_loans_approver
        FOREIGN KEY (approved_by) REFERENCES users(id)
        ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT chk_due_date
        CHECK (due_date >= loan_date),
    INDEX idx_loans_user_id (user_id),
    INDEX idx_loans_status (status)
) ENGINE=InnoDB;


-- ------------------------------------------------------------
-- 5. LOAN_ITEMS
-- ------------------------------------------------------------
CREATE TABLE loan_items (
    id                INT UNSIGNED NOT NULL AUTO_INCREMENT,
    loan_id           INT UNSIGNED NOT NULL,
    tool_id           INT UNSIGNED NOT NULL,
    quantity          INT UNSIGNED NOT NULL DEFAULT 1,
    quantity_returned INT UNSIGNED NOT NULL DEFAULT 0
                      COMMENT 'Berapa unit yang sudah dikembalikan (partial return support)',
    PRIMARY KEY (id),
    CONSTRAINT fk_loan_items_loan
        FOREIGN KEY (loan_id) REFERENCES loans(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_loan_items_tool
        FOREIGN KEY (tool_id) REFERENCES tools(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    UNIQUE KEY uq_loan_tool (loan_id, tool_id),
    CONSTRAINT chk_quantity     CHECK (quantity >= 1),
    CONSTRAINT chk_qty_returned CHECK (quantity_returned <= quantity)
) ENGINE=InnoDB;


-- ------------------------------------------------------------
-- 6. RETURNS
-- ------------------------------------------------------------
CREATE TABLE returns (
    id           INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    loan_id      INT UNSIGNED  NOT NULL,
    processed_by INT UNSIGNED  NOT NULL  COMMENT 'Petugas yang proses sesi ini',
    return_date  DATE          NOT NULL,
    late_days    INT UNSIGNED  NOT NULL DEFAULT 0,
    fine_per_day DECIMAL(10,2) NOT NULL DEFAULT 0.00,
    total_fine   DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    notes        TEXT,
    created_at   DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    CONSTRAINT fk_returns_loan
        FOREIGN KEY (loan_id) REFERENCES loans(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_returns_petugas
        FOREIGN KEY (processed_by) REFERENCES users(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    INDEX idx_returns_loan_id (loan_id)
) ENGINE=InnoDB;


-- ------------------------------------------------------------
-- 7. RETURN_ITEMS
-- ------------------------------------------------------------
CREATE TABLE return_items (
    id                  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    return_id           INT UNSIGNED NOT NULL,
    loan_item_id        INT UNSIGNED NOT NULL,
    quantity_returned   INT UNSIGNED NOT NULL DEFAULT 1,
    condition_on_return ENUM('baik','rusak_ringan','rusak_berat')
                        NOT NULL DEFAULT 'baik',
    PRIMARY KEY (id),
    CONSTRAINT fk_ri_return
        FOREIGN KEY (return_id) REFERENCES returns(id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_ri_loan_item
        FOREIGN KEY (loan_item_id) REFERENCES loan_items(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    UNIQUE KEY uq_return_loanitem (return_id, loan_item_id),
    CONSTRAINT chk_ri_qty CHECK (quantity_returned >= 1)
) ENGINE=InnoDB;


-- ------------------------------------------------------------
-- 8. ACTIVITY_LOGS
-- ------------------------------------------------------------
CREATE TABLE activity_logs (
    id          INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    user_id     INT UNSIGNED  NULL,
    action      VARCHAR(100)  NOT NULL,
    description TEXT,
    ip_address  VARCHAR(45)   COMMENT 'IPv4 atau IPv6',
    user_agent  TEXT,          -- [NEW v2.0.0] Tambahan dari middleware
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_logs_user_id (user_id),
    INDEX idx_logs_action (action),
    INDEX idx_logs_created_at (created_at)
) ENGINE=InnoDB;
