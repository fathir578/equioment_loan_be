-- ============================================================
--  APLIKASI PEMINJAMAN ALAT — schema.sql
--  Versi final setelah semua bug fix
--
--  Bug fixes dari review:
--  [Bug 4] condition_on_return dipindah ke return_items (per alat)
--  [Bug 5] CHECK constraint: approved_by != user_id
--  [Bug 6] Tambah return_items + loan_items.quantity_returned
--           + status 'partial_returned' di loans
-- ============================================================

CREATE DATABASE IF NOT EXISTS db_peminjaman_alat
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE db_peminjaman_alat;

-- ------------------------------------------------------------
-- 1. USERS
-- ------------------------------------------------------------
CREATE TABLE users (
    id            INT UNSIGNED     NOT NULL AUTO_INCREMENT,
    username      VARCHAR(50)      NOT NULL UNIQUE,
    email         VARCHAR(100)     NOT NULL UNIQUE,
    password_hash VARCHAR(255)     NOT NULL,
    role          ENUM('admin','petugas','peminjam') NOT NULL DEFAULT 'peminjam',
    qr_token      VARCHAR(64)      NOT NULL UNIQUE
                  COMMENT 'Token unik yang di-encode jadi QR Card user',
    is_active     TINYINT(1)       NOT NULL DEFAULT 1,
    created_at    DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at    DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP
                  ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_users_role (role),
    INDEX idx_users_qr_token (qr_token)
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
-- 3. TOOLS
-- ------------------------------------------------------------
CREATE TABLE tools (
    id              INT UNSIGNED  NOT NULL AUTO_INCREMENT,
    category_id     INT UNSIGNED  NOT NULL,
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
    CONSTRAINT chk_stock CHECK (stock_available <= stock_total),
    INDEX idx_tools_qr_code (qr_code),
    INDEX idx_tools_category (category_id),
    INDEX idx_tools_is_active (is_active)
) ENGINE=InnoDB;


-- ------------------------------------------------------------
-- 4. LOANS
--
--  [Bug 5] CHECK approved_by != user_id — guard terakhir di DB.
--    Meskipun layer API sudah validasi, DB adalah safety net
--    kalau ada bug atau bypass di level aplikasi.
--
--  [Bug 6] Status diperluas:
--    pending          → menunggu persetujuan
--    approved         → disetujui, sedang dipinjam
--    rejected         → ditolak
--    partial_returned → sebagian alat sudah dikembalikan
--    returned         → semua alat sudah dikembalikan
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
--
--  [Bug 6] quantity_returned melacak berapa unit per alat
--    yang sudah dikembalikan.
--    → quantity_returned = 0        : belum ada yang dikembalikan
--    → 0 < quantity_returned < qty  : partial
--    → quantity_returned = quantity : fully returned
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
-- 6. RETURNS  (satu sesi pengembalian)
--
--  [Bug 6] Satu loan BISA punya lebih dari satu return.
--    Contoh: pinjam 3 alat, kembalikan 2 hari ini (return #1),
--    kembalikan sisanya minggu depan (return #2).
--    Karena itu tidak ada UNIQUE KEY di loan_id.
--
--  [Bug 4] condition_on_return TIDAK ada di sini.
--    Kondisi adalah per-alat, bukan per-sesi.
--    Ada di return_items.
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
-- 7. RETURN_ITEMS  [TABEL BARU — Bug 6 + Bug 4]
--
--  Detail per-alat dalam satu sesi pengembalian.
--
--  [Bug 4] condition_on_return ada di sini karena tiap alat
--    bisa punya kondisi berbeda saat dikembalikan.
--    Trigger akan membaca ini dan update tools.condition,
--    dengan aturan: hanya DOWNGRADE kondisi, tidak pernah
--    auto-upgrade (alat rusak tidak tiba-tiba jadi "baik").
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
    -- Satu loan_item hanya bisa muncul sekali per sesi return
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
    created_at  DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id),
    INDEX idx_logs_user_id (user_id),
    INDEX idx_logs_action (action),
    INDEX idx_logs_created_at (created_at)
) ENGINE=InnoDB;
