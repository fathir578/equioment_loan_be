-- ============================================================
--  APLIKASI PEMINJAMAN ALAT — triggers.sql
--  Versi final setelah semua bug fix
--
--  Fix tambahan:
--  SIGNAL SET MESSAGE_TEXT tidak bisa pakai CONCAT() langsung.
--  Solusi: simpan ke variabel DECLARE dulu, baru pakai di MESSAGE_TEXT.
-- ============================================================

USE db_peminjaman_alat;

DELIMITER $$

-- ============================================================
-- TRIGGER 1: Validasi role approved_by SEBELUM loan diupdate
-- [Bug 5] Hanya petugas/admin yang boleh approve
-- ============================================================
CREATE TRIGGER trg_validate_loan_approver
BEFORE UPDATE ON loans
FOR EACH ROW
BEGIN
    DECLARE v_approver_role   VARCHAR(10);
    DECLARE v_approver_active TINYINT(1);
    DECLARE v_msg             VARCHAR(255);

    IF NEW.approved_by IS NOT NULL AND
       (OLD.approved_by IS NULL OR NEW.approved_by != OLD.approved_by) THEN

        SELECT role, is_active
        INTO   v_approver_role, v_approver_active
        FROM   users
        WHERE  id = NEW.approved_by;

        IF v_approver_role IS NULL THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Approval gagal: approver tidak ditemukan.';
        END IF;

        IF v_approver_active = 0 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Approval gagal: akun approver tidak aktif.';
        END IF;

        IF v_approver_role NOT IN ('petugas', 'admin') THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Approval gagal: hanya Petugas atau Admin yang berhak menyetujui peminjaman.';
        END IF;

        IF NEW.approved_by = NEW.user_id THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Approval gagal: peminjam tidak boleh menyetujui loan miliknya sendiri.';
        END IF;

    END IF;

    IF NEW.status = 'approved' AND OLD.status IN ('returned','partial_returned','rejected') THEN
        -- Simpan pesan ke variabel dulu, baru pakai di SIGNAL
        SET v_msg = CONCAT('Transisi status tidak valid dari "', OLD.status, '".');
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = v_msg;
    END IF;

END$$


-- ============================================================
-- TRIGGER 2: Kurangi stok saat loan diapprove
-- [Bug 1] Cursor + SIGNAL per item (tidak silent skip)
-- [Bug 3] SELECT FOR UPDATE untuk lock row (anti race condition)
-- ============================================================
CREATE TRIGGER trg_decrease_stock_on_approve
AFTER UPDATE ON loans
FOR EACH ROW
BEGIN
    DECLARE v_tool_id   INT UNSIGNED;
    DECLARE v_qty       INT UNSIGNED;
    DECLARE v_stock     INT UNSIGNED;
    DECLARE v_tool_name VARCHAR(150);
    DECLARE v_done      TINYINT DEFAULT 0;
    DECLARE v_msg       VARCHAR(255);

    DECLARE cur_items CURSOR FOR
        SELECT tool_id, quantity
        FROM   loan_items
        WHERE  loan_id = NEW.id;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;

    IF OLD.status != 'approved' AND NEW.status = 'approved' THEN

        -- Fase 1: Lock + validasi stok semua item
        OPEN cur_items;
        validate_loop: LOOP
            FETCH cur_items INTO v_tool_id, v_qty;
            IF v_done THEN LEAVE validate_loop; END IF;

            SELECT stock_available, name
            INTO   v_stock, v_tool_name
            FROM   tools
            WHERE  id = v_tool_id
            FOR UPDATE;

            IF v_stock < v_qty THEN
                CLOSE cur_items;
                -- Simpan ke variabel dulu, SIGNAL tidak bisa pakai CONCAT langsung
                SET v_msg = CONCAT(
                    'Approval gagal: stok "', v_tool_name, '" tidak mencukupi. ',
                    'Tersedia: ', v_stock, ', diminta: ', v_qty, '.'
                );
                SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = v_msg;
            END IF;

        END LOOP validate_loop;
        CLOSE cur_items;

        -- Fase 2: Update stok (aman karena Fase 1 lolos + lock aktif)
        UPDATE tools t
        INNER JOIN loan_items li ON li.tool_id = t.id
        SET t.stock_available = t.stock_available - li.quantity
        WHERE li.loan_id = NEW.id;

        INSERT INTO activity_logs (user_id, action, description)
        VALUES (
            NEW.approved_by,
            'APPROVE_LOAN',
            CONCAT('Loan #', NEW.id, ' disetujui. Stok semua alat dikurangi.')
        );

    END IF;
END$$


-- ============================================================
-- TRIGGER 3: Kembalikan stok jika loan di-reject setelah approved
-- ============================================================
CREATE TRIGGER trg_restore_stock_on_reject
AFTER UPDATE ON loans
FOR EACH ROW
BEGIN
    IF OLD.status = 'approved' AND NEW.status = 'rejected' THEN
        UPDATE tools t
        INNER JOIN loan_items li ON li.tool_id = t.id
        SET t.stock_available = LEAST(
            t.stock_available + li.quantity,
            t.stock_total
        )
        WHERE li.loan_id = NEW.id;

        INSERT INTO activity_logs (user_id, action, description)
        VALUES (
            NEW.approved_by,
            'REJECT_LOAN',
            CONCAT('Loan #', NEW.id, ' ditolak setelah approved. Stok dikembalikan.')
        );
    END IF;
END$$


-- ============================================================
-- TRIGGER 4: Proses return_items setelah INSERT
-- [Bug 4] Update tools.condition — hanya downgrade
-- [Bug 6] Support partial return — update quantity_returned
-- ============================================================
CREATE TRIGGER trg_process_return_item
AFTER INSERT ON return_items
FOR EACH ROW
BEGIN
    DECLARE v_tool_id             INT UNSIGNED;
    DECLARE v_qty_pinjam          INT UNSIGNED;
    DECLARE v_qty_sudah_kembali   INT UNSIGNED;
    DECLARE v_sisa                INT UNSIGNED;
    DECLARE v_loan_id             INT UNSIGNED;
    DECLARE v_current_condition   VARCHAR(15);
    DECLARE v_new_condition       VARCHAR(15);
    DECLARE v_remaining           INT DEFAULT 0;
    DECLARE v_processed_by        INT UNSIGNED;
    DECLARE v_msg                 VARCHAR(255);

    -- Ambil data loan_item + lock baris
    SELECT li.tool_id, li.quantity, li.quantity_returned, li.loan_id
    INTO   v_tool_id, v_qty_pinjam, v_qty_sudah_kembali, v_loan_id
    FROM   loan_items li
    WHERE  li.id = NEW.loan_item_id
    FOR UPDATE;

    -- Validasi: tidak boleh kembalikan lebih dari sisa
    SET v_sisa = v_qty_pinjam - v_qty_sudah_kembali;

    IF NEW.quantity_returned > v_sisa THEN
        SET v_msg = CONCAT(
            'Pengembalian gagal: jumlah dikembalikan (',
            NEW.quantity_returned,
            ') melebihi sisa belum kembali (', v_sisa, ').'
        );
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = v_msg;
    END IF;

    -- Update quantity_returned di loan_items
    UPDATE loan_items
    SET quantity_returned = quantity_returned + NEW.quantity_returned
    WHERE id = NEW.loan_item_id;

    -- Kembalikan stok alat
    UPDATE tools
    SET stock_available = LEAST(stock_available + NEW.quantity_returned, stock_total)
    WHERE id = v_tool_id;

    -- [Bug 4] Update kondisi alat — hanya DOWNGRADE, tidak pernah upgrade otomatis
    SELECT `condition` INTO v_current_condition
    FROM tools WHERE id = v_tool_id;

    SET v_new_condition = CASE
        WHEN NEW.condition_on_return = 'rusak_berat'
            THEN 'rusak_berat'
        WHEN NEW.condition_on_return = 'rusak_ringan' AND v_current_condition = 'baik'
            THEN 'rusak_ringan'
        ELSE v_current_condition
    END;

    IF v_new_condition != v_current_condition THEN
        UPDATE tools
        SET
            `condition` = v_new_condition,
            -- Rusak berat → otomatis nonaktif, harus direview Admin
            is_active = CASE WHEN v_new_condition = 'rusak_berat' THEN 0 ELSE is_active END
        WHERE id = v_tool_id;

        -- Ambil processed_by dari tabel returns
        SELECT processed_by INTO v_processed_by
        FROM returns WHERE id = NEW.return_id;

        INSERT INTO activity_logs (user_id, action, description)
        VALUES (
            v_processed_by,
            'TOOL_CONDITION_DOWNGRADE',
            CONCAT(
                'Kondisi alat #', v_tool_id,
                ' turun dari "', v_current_condition,
                '" ke "', v_new_condition, '".'
            )
        );
    END IF;

    -- [Bug 6] Cek apakah semua item loan sudah fully returned
    SELECT processed_by INTO v_processed_by
    FROM returns WHERE id = NEW.return_id;

    SELECT COUNT(*) INTO v_remaining
    FROM loan_items
    WHERE loan_id = v_loan_id
      AND quantity_returned < quantity;

    IF v_remaining = 0 THEN
        UPDATE loans SET status = 'returned' WHERE id = v_loan_id;
        INSERT INTO activity_logs (user_id, action, description)
        VALUES (
            v_processed_by, 'LOAN_FULLY_RETURNED',
            CONCAT('Semua alat Loan #', v_loan_id, ' telah dikembalikan.')
        );
    ELSE
        UPDATE loans SET status = 'partial_returned' WHERE id = v_loan_id;
        INSERT INTO activity_logs (user_id, action, description)
        VALUES (
            v_processed_by, 'LOAN_PARTIAL_RETURNED',
            CONCAT('Loan #', v_loan_id, ': ', v_remaining, ' item belum dikembalikan.')
        );
    END IF;

END$$


-- ============================================================
-- TRIGGER 5: Auto-log saat user baru dibuat
-- ============================================================
CREATE TRIGGER trg_log_new_user
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO activity_logs (user_id, action, description)
    VALUES (
        NEW.id,
        'USER_CREATED',
        CONCAT('Akun baru: ', NEW.username, ' (role: ', NEW.role, ')')
    );
END$$


-- ============================================================
-- TRIGGER 6: Validasi stok SEBELUM loan_item diinsert
-- ============================================================
CREATE TRIGGER trg_check_stock_before_loan_item
BEFORE INSERT ON loan_items
FOR EACH ROW
BEGIN
    DECLARE v_available INT UNSIGNED;
    DECLARE v_tool_name VARCHAR(150);
    DECLARE v_is_active TINYINT(1);
    DECLARE v_msg       VARCHAR(255);

    SELECT stock_available, name, is_active
    INTO   v_available, v_tool_name, v_is_active
    FROM   tools
    WHERE  id = NEW.tool_id;

    IF v_is_active = 0 THEN
        -- Simpan ke variabel dulu
        SET v_msg = CONCAT('Alat "', v_tool_name, '" tidak aktif dan tidak bisa dipinjam.');
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = v_msg;
    END IF;

    IF v_available < NEW.quantity THEN
        SET v_msg = CONCAT(
            'Stok "', v_tool_name, '" tidak mencukupi. ',
            'Tersedia: ', v_available, ', diminta: ', NEW.quantity, '.'
        );
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = v_msg;
    END IF;
END$$


DELIMITER ;
