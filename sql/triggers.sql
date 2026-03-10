-- triggers.sql (MariaDB compatible)
USE db_peminjaman_alat;

DELIMITER $$

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
            SIGNAL SQLSTATE "45000"
            SET MESSAGE_TEXT = "Approval gagal: approver tidak ditemukan.";
        END IF;

        IF v_approver_active = 0 THEN
            SIGNAL SQLSTATE "45000"
            SET MESSAGE_TEXT = "Approval gagal: akun approver tidak aktif.";
        END IF;

        IF v_approver_role NOT IN ("petugas", "admin") THEN
            SIGNAL SQLSTATE "45000"
            SET MESSAGE_TEXT = "Approval gagal: hanya Petugas atau Admin yang boleh approve.";
        END IF;

        IF NEW.approved_by = NEW.user_id THEN
            SIGNAL SQLSTATE "45000"
            SET MESSAGE_TEXT = "Approval gagal: peminjam tidak boleh approve loan sendiri.";
        END IF;

    END IF;

    IF NEW.status = "approved" AND OLD.status IN ("returned","partial_returned","rejected") THEN
        SIGNAL SQLSTATE "45000"
        SET MESSAGE_TEXT = "Transisi status tidak valid.";
    END IF;

END$$


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

    IF OLD.status != "approved" AND NEW.status = "approved" THEN

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
                SET v_msg = CONCAT("Stok ", v_tool_name, " tidak cukup. Tersedia: ", v_stock, " diminta: ", v_qty);
                SIGNAL SQLSTATE "45000"
                SET MESSAGE_TEXT = v_msg;
            END IF;

        END LOOP validate_loop;
        CLOSE cur_items;

        UPDATE tools t
        INNER JOIN loan_items li ON li.tool_id = t.id
        SET t.stock_available = t.stock_available - li.quantity
        WHERE li.loan_id = NEW.id;

        INSERT INTO activity_logs (user_id, action, description)
        VALUES (NEW.approved_by, "APPROVE_LOAN",
                CONCAT("Loan #", NEW.id, " disetujui."));

    END IF;
END$$


CREATE TRIGGER trg_restore_stock_on_reject
AFTER UPDATE ON loans
FOR EACH ROW
BEGIN
    IF OLD.status = "approved" AND NEW.status = "rejected" THEN
        UPDATE tools t
        INNER JOIN loan_items li ON li.tool_id = t.id
        SET t.stock_available = LEAST(t.stock_available + li.quantity, t.stock_total)
        WHERE li.loan_id = NEW.id;

        INSERT INTO activity_logs (user_id, action, description)
        VALUES (NEW.approved_by, "REJECT_LOAN",
                CONCAT("Loan #", NEW.id, " ditolak. Stok dikembalikan."));
    END IF;
END$$


CREATE TRIGGER trg_process_return_item
AFTER INSERT ON return_items
FOR EACH ROW
BEGIN
    DECLARE v_tool_id           INT UNSIGNED;
    DECLARE v_qty_pinjam        INT UNSIGNED;
    DECLARE v_qty_kembali       INT UNSIGNED;
    DECLARE v_sisa              INT UNSIGNED;
    DECLARE v_loan_id           INT UNSIGNED;
    DECLARE v_current_cond      VARCHAR(15);
    DECLARE v_new_cond          VARCHAR(15);
    DECLARE v_remaining         INT DEFAULT 0;
    DECLARE v_processed_by      INT UNSIGNED;
    DECLARE v_msg               VARCHAR(255);

    SELECT li.tool_id, li.quantity, li.quantity_returned, li.loan_id
    INTO   v_tool_id, v_qty_pinjam, v_qty_kembali, v_loan_id
    FROM   loan_items li
    WHERE  li.id = NEW.loan_item_id
    FOR UPDATE;

    SET v_sisa = v_qty_pinjam - v_qty_kembali;

    IF NEW.quantity_returned > v_sisa THEN
        SET v_msg = CONCAT("Jumlah dikembalikan ", NEW.quantity_returned, " melebihi sisa ", v_sisa);
        SIGNAL SQLSTATE "45000"
        SET MESSAGE_TEXT = v_msg;
    END IF;

    UPDATE loan_items
    SET quantity_returned = quantity_returned + NEW.quantity_returned
    WHERE id = NEW.loan_item_id;

    UPDATE tools
    SET stock_available = LEAST(stock_available + NEW.quantity_returned, stock_total)
    WHERE id = v_tool_id;

    SELECT `condition` INTO v_current_cond FROM tools WHERE id = v_tool_id;

    SET v_new_cond = CASE
        WHEN NEW.condition_on_return = "rusak_berat" THEN "rusak_berat"
        WHEN NEW.condition_on_return = "rusak_ringan" AND v_current_cond = "baik" THEN "rusak_ringan"
        ELSE v_current_cond
    END;

    IF v_new_cond != v_current_cond THEN
        UPDATE tools
        SET `condition` = v_new_cond,
            is_active   = CASE WHEN v_new_cond = "rusak_berat" THEN 0 ELSE is_active END
        WHERE id = v_tool_id;

        SELECT processed_by INTO v_processed_by FROM returns WHERE id = NEW.return_id;

        INSERT INTO activity_logs (user_id, action, description)
        VALUES (v_processed_by, "TOOL_CONDITION_DOWNGRADE",
                CONCAT("Alat #", v_tool_id, " kondisi turun ke ", v_new_cond));
    END IF;

    SELECT processed_by INTO v_processed_by FROM returns WHERE id = NEW.return_id;

    SELECT COUNT(*) INTO v_remaining
    FROM loan_items
    WHERE loan_id = v_loan_id AND quantity_returned < quantity;

    IF v_remaining = 0 THEN
        UPDATE loans SET status = "returned" WHERE id = v_loan_id;
        INSERT INTO activity_logs (user_id, action, description)
        VALUES (v_processed_by, "LOAN_FULLY_RETURNED",
                CONCAT("Semua alat Loan #", v_loan_id, " dikembalikan."));
    ELSE
        UPDATE loans SET status = "partial_returned" WHERE id = v_loan_id;
        INSERT INTO activity_logs (user_id, action, description)
        VALUES (v_processed_by, "LOAN_PARTIAL_RETURNED",
                CONCAT("Loan #", v_loan_id, ": ", v_remaining, " item belum kembali."));
    END IF;

END$$


CREATE TRIGGER trg_log_new_user
AFTER INSERT ON users
FOR EACH ROW
BEGIN
    INSERT INTO activity_logs (user_id, action, description)
    VALUES (NEW.id, "USER_CREATED",
            CONCAT("Akun baru: ", NEW.username, " (", NEW.role, ")"));
END$$


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
    FROM   tools WHERE id = NEW.tool_id;

    IF v_is_active = 0 THEN
        SET v_msg = CONCAT("Alat ", v_tool_name, " tidak aktif.");
        SIGNAL SQLSTATE "45000"
        SET MESSAGE_TEXT = v_msg;
    END IF;

    IF v_available < NEW.quantity THEN
        SET v_msg = CONCAT("Stok ", v_tool_name, " kurang. Tersedia: ", v_available);
        SIGNAL SQLSTATE "45000"
        SET MESSAGE_TEXT = v_msg;
    END IF;
END$$


DELIMITER ;
