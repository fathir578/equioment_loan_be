-- ============================================================
--  APLIKASI PEMINJAMAN ALAT — stored_procedures.sql
--  Versi final setelah semua bug fix
--
--  Bug fixes dari versi sebelumnya:
--  [Bug 2] LEAVE ke nama procedure → ganti dengan label proc_body
--  [Bug 2] p_message ghost variable di sp_get_user_by_qr → dihapus
--  [Bug 2] Tidak ada NOT FOUND handler → ditambahkan
--  [Bug 2] EXIT HANDLER tanpa GET DIAGNOSTICS → ditambahkan
--  [Bug 6] sp_process_return ditulis ulang untuk support partial return
--          + menggunakan return_items bukan langsung ke returns
-- ============================================================



DELIMITER $$

-- ============================================================
-- FUNCTION: Hitung denda keterlambatan
-- ============================================================
CREATE FUNCTION fn_calculate_fine(
    p_due_date     DATE,
    p_return_date  DATE,
    p_fine_per_day DECIMAL(10,2)
)
RETURNS DECIMAL(10,2)
DETERMINISTIC
BEGIN
    DECLARE late_days INT DEFAULT 0;

    SET late_days = DATEDIFF(p_return_date, p_due_date);

    IF late_days <= 0 THEN
        RETURN 0.00;
    END IF;

    RETURN late_days * p_fine_per_day;
END$$


-- ============================================================
-- PROCEDURE 1: Buat peminjaman baru
--
--  [Bug 2] LEAVE sp_create_loan → LEAVE proc_body (label valid)
--  [Bug 2] Validasi sebelum START TRANSACTION
--  [Bug 2] GET DIAGNOSTICS untuk tangkap pesan error asli
-- ============================================================
CREATE PROCEDURE sp_create_loan(
    IN  p_user_id    INT UNSIGNED,
    IN  p_loan_date  DATE,
    IN  p_due_date   DATE,
    IN  p_notes      TEXT,
    IN  p_items_json JSON,      -- '[{"tool_id":1,"qty":2},{"tool_id":3,"qty":1}]'
    OUT p_loan_id    INT UNSIGNED,
    OUT p_message    VARCHAR(255)
)
proc_body: BEGIN
    DECLARE v_loan_id    INT UNSIGNED DEFAULT 0;
    DECLARE v_tool_id    INT UNSIGNED;
    DECLARE v_qty        INT UNSIGNED;
    DECLARE v_stock      INT UNSIGNED;
    DECLARE v_item_count INT;
    DECLARE v_i          INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 @err_msg = MESSAGE_TEXT;
        ROLLBACK;
        SET p_loan_id = 0;
        SET p_message = CONCAT('Error: ', IFNULL(@err_msg, 'Unknown database error'));
    END;

    SET p_loan_id = 0;
    SET p_message = '';

    -- Validasi SEBELUM buka transaksi
    IF p_due_date < p_loan_date THEN
        SET p_message = 'Tanggal kembali tidak boleh sebelum tanggal pinjam.';
        LEAVE proc_body;
    END IF;

    IF p_items_json IS NULL OR JSON_LENGTH(p_items_json) = 0 THEN
        SET p_message = 'Minimal satu alat harus dipilih.';
        LEAVE proc_body;
    END IF;

    START TRANSACTION;

    INSERT INTO loans (user_id, loan_date, due_date, status, notes)
    VALUES (p_user_id, p_loan_date, p_due_date, 'pending', p_notes);

    SET v_loan_id    = LAST_INSERT_ID();
    SET v_item_count = JSON_LENGTH(p_items_json);

    WHILE v_i < v_item_count DO
        SET v_tool_id = JSON_UNQUOTE(JSON_EXTRACT(p_items_json, CONCAT('$[', v_i, '].tool_id')));
        SET v_qty     = JSON_UNQUOTE(JSON_EXTRACT(p_items_json, CONCAT('$[', v_i, '].qty')));

        -- Lock baris tool sebelum cek stok (mencegah race condition)
        SELECT stock_available INTO v_stock
        FROM   tools
        WHERE  id = v_tool_id AND is_active = 1
        FOR UPDATE;

        IF v_stock IS NULL THEN
            ROLLBACK;
            SET p_loan_id = 0;
            SET p_message = CONCAT('Alat ID ', v_tool_id, ' tidak ditemukan atau tidak aktif.');
            LEAVE proc_body;
        END IF;

        IF v_stock < v_qty THEN
            ROLLBACK;
            SET p_loan_id = 0;
            SET p_message = CONCAT(
                'Stok alat ID ', v_tool_id, ' tidak mencukupi. ',
                'Tersedia: ', v_stock, ', diminta: ', v_qty
            );
            LEAVE proc_body;
        END IF;

        -- trg_check_stock_before_loan_item akan validasi ulang di sini
        INSERT INTO loan_items (loan_id, tool_id, quantity)
        VALUES (v_loan_id, v_tool_id, v_qty);

        SET v_i = v_i + 1;
    END WHILE;

    COMMIT;
    SET p_loan_id = v_loan_id;
    SET p_message = 'Peminjaman berhasil diajukan, menunggu persetujuan petugas.';
END$$


-- ============================================================
-- PROCEDURE 2: Proses pengembalian (support partial return)
--
--  [Bug 6] Ditulis ulang dari scratch.
--    Parameter p_items_json berisi alat apa saja yang dikembalikan
--    dalam sesi ini, beserta kondisinya.
--
--  Format p_items_json:
--    '[{"loan_item_id":1,"qty_returned":2,"condition":"baik"},
--      {"loan_item_id":2,"qty_returned":1,"condition":"rusak_ringan"}]'
--
--  Flow:
--    1. Validasi loan harus berstatus approved/partial_returned
--    2. INSERT ke returns (buat sesi pengembalian)
--    3. INSERT ke return_items per alat yang dikembalikan
--       → trigger trg_process_return_item akan otomatis:
--           - update loan_items.quantity_returned
--           - update tools.stock_available
--           - update tools.condition (hanya downgrade) [Bug 4]
--           - update loans.status (partial/returned) [Bug 6]
-- ============================================================
CREATE PROCEDURE sp_process_return(
    IN  p_loan_id      INT UNSIGNED,
    IN  p_processed_by INT UNSIGNED,
    IN  p_return_date  DATE,
    IN  p_fine_per_day DECIMAL(10,2),
    IN  p_items_json   JSON,
    IN  p_notes        TEXT,
    OUT p_return_id    INT UNSIGNED,
    OUT p_late_days    INT,
    OUT p_total_fine   DECIMAL(10,2),
    OUT p_message      VARCHAR(255)
)
proc_body: BEGIN
    DECLARE v_due_date     DATE;
    DECLARE v_status       VARCHAR(20);
    DECLARE v_late_days    INT DEFAULT 0;
    DECLARE v_total_fine   DECIMAL(10,2) DEFAULT 0.00;
    DECLARE v_item_count   INT;
    DECLARE v_i            INT DEFAULT 0;
    DECLARE v_loan_item_id INT UNSIGNED;
    DECLARE v_qty_ret      INT UNSIGNED;
    DECLARE v_condition    VARCHAR(15);

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        GET DIAGNOSTICS CONDITION 1 @err_msg = MESSAGE_TEXT;
        ROLLBACK;
        SET p_return_id = 0;
        SET p_message   = CONCAT('Error: ', IFNULL(@err_msg, 'Unknown database error'));
    END;

    SET p_return_id  = 0;
    SET p_late_days  = 0;
    SET p_total_fine = 0.00;
    SET p_message    = '';

    -- Validasi input
    IF p_items_json IS NULL OR JSON_LENGTH(p_items_json) = 0 THEN
        SET p_message = 'Minimal satu alat harus dipilih untuk dikembalikan.';
        LEAVE proc_body;
    END IF;

    START TRANSACTION;

    -- Ambil dan lock baris loan
    SELECT due_date, status INTO v_due_date, v_status
    FROM   loans
    WHERE  id = p_loan_id
    FOR UPDATE;

    IF v_status IS NULL THEN
        ROLLBACK;
        SET p_message = CONCAT('Loan #', p_loan_id, ' tidak ditemukan.');
        LEAVE proc_body;
    END IF;

    -- [Bug 6] Loan harus berstatus approved ATAU partial_returned
    IF v_status NOT IN ('approved', 'partial_returned') THEN
        ROLLBACK;
        SET p_message = CONCAT(
            'Loan #', p_loan_id, ' tidak bisa diproses. ',
            'Status saat ini: "', v_status, '". ',
            'Hanya status "approved" atau "partial_returned" yang bisa dikembalikan.'
        );
        LEAVE proc_body;
    END IF;

    -- Hitung denda berdasarkan tanggal sesi ini
    SET v_late_days  = GREATEST(0, DATEDIFF(p_return_date, v_due_date));
    SET v_total_fine = fn_calculate_fine(v_due_date, p_return_date, p_fine_per_day);

    -- Buat sesi pengembalian di tabel returns
    INSERT INTO returns (loan_id, processed_by, return_date, late_days, fine_per_day, total_fine, notes)
    VALUES (p_loan_id, p_processed_by, p_return_date, v_late_days, p_fine_per_day, v_total_fine, p_notes);

    SET p_return_id  = LAST_INSERT_ID();
    SET v_item_count = JSON_LENGTH(p_items_json);

    -- Insert setiap alat yang dikembalikan dalam sesi ini
    -- Trigger trg_process_return_item akan otomatis handle semua side effects
    WHILE v_i < v_item_count DO
        SET v_loan_item_id = JSON_UNQUOTE(JSON_EXTRACT(p_items_json, CONCAT('$[', v_i, '].loan_item_id')));
        SET v_qty_ret      = JSON_UNQUOTE(JSON_EXTRACT(p_items_json, CONCAT('$[', v_i, '].qty_returned')));
        SET v_condition    = JSON_UNQUOTE(JSON_EXTRACT(p_items_json, CONCAT('$[', v_i, '].condition')));

        -- Validasi nilai condition
        IF v_condition NOT IN ('baik', 'rusak_ringan', 'rusak_berat') THEN
            ROLLBACK;
            SET p_return_id = 0;
            SET p_message = CONCAT(
                'Nilai kondisi tidak valid: "', v_condition,
                '". Pilihan: baik, rusak_ringan, rusak_berat.'
            );
            LEAVE proc_body;
        END IF;

        -- Trigger trg_process_return_item jalan di sini
        INSERT INTO return_items (return_id, loan_item_id, quantity_returned, condition_on_return)
        VALUES (p_return_id, v_loan_item_id, v_qty_ret, v_condition);

        SET v_i = v_i + 1;
    END WHILE;

    COMMIT;
    SET p_late_days  = v_late_days;
    SET p_total_fine = v_total_fine;
    SET p_message    = CONCAT(
        'Pengembalian berhasil diproses.',
        IF(v_late_days > 0,
            CONCAT(' Terlambat ', v_late_days, ' hari. Denda: Rp', FORMAT(v_total_fine, 0), '.'),
            ' Tidak ada denda.'
        )
    );
END$$


-- ============================================================
-- PROCEDURE 3: Lookup user by QR Token
--
--  [Bug 2] Hapus p_message ghost variable
--  [Bug 2] Tambah NOT FOUND handler
-- ============================================================
CREATE PROCEDURE sp_get_user_by_qr(
    IN  p_qr_token VARCHAR(64),
    OUT p_found    TINYINT,
    OUT p_user_id  INT UNSIGNED,
    OUT p_username VARCHAR(50),
    OUT p_role     VARCHAR(20)
)
BEGIN
    -- [Bug 2] Tanpa handler ini, SELECT INTO yang tidak menemukan baris
    -- akan raise SQLSTATE '02000' yang tidak tertangkap
    DECLARE CONTINUE HANDLER FOR NOT FOUND
    BEGIN
        SET p_found    = 0;
        SET p_user_id  = NULL;
        SET p_username = NULL;
        SET p_role     = NULL;
    END;

    SET p_found = 0;

    SELECT id, username, role
    INTO   p_user_id, p_username, p_role
    FROM   users
    WHERE  qr_token = p_qr_token
      AND  is_active = 1
    LIMIT 1;

    IF p_user_id IS NOT NULL THEN
        SET p_found = 1;
    END IF;
    -- Tidak ada p_message — caller yang handle berdasarkan p_found
END$$


-- ============================================================
-- PROCEDURE 4: Lookup alat by QR Code
--
--  [Bug 2] Tambah NOT FOUND handler
-- ============================================================
CREATE PROCEDURE sp_get_tool_by_qr(
    IN  p_qr_code   VARCHAR(64),
    OUT p_found     TINYINT,
    OUT p_tool_id   INT UNSIGNED,
    OUT p_tool_name VARCHAR(150),
    OUT p_available INT UNSIGNED
)
BEGIN
    DECLARE CONTINUE HANDLER FOR NOT FOUND
    BEGIN
        SET p_found     = 0;
        SET p_tool_id   = NULL;
        SET p_tool_name = NULL;
        SET p_available = NULL;
    END;

    SET p_found = 0;

    SELECT id, name, stock_available
    INTO   p_tool_id, p_tool_name, p_available
    FROM   tools
    WHERE  qr_code = p_qr_code
      AND  is_active = 1
    LIMIT 1;

    IF p_tool_id IS NOT NULL THEN
        SET p_found = 1;
    END IF;
END$$


DELIMITER ;
