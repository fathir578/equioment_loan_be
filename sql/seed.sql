-- ============================================================
--  APLIKASI PEMINJAMAN ALAT — seed.sql
--  Data awal untuk testing (v1.1.6)
--  Disesuaikan dengan struktur tabel Django Migrations
-- ============================================================



SET FOREIGN_KEY_CHECKS = 0;

-- Bersihkan data lama
DELETE FROM token_blacklist_blacklistedtoken;
DELETE FROM token_blacklist_outstandingtoken;
DELETE FROM activity_logs;
DELETE FROM return_items;
DELETE FROM returns;
DELETE FROM loan_items;
DELETE FROM loans;
DELETE FROM tools;
DELETE FROM categories;
DELETE FROM users;

SET FOREIGN_KEY_CHECKS = 1;

-- 1. DATA CATEGORIES
-- Note: Django biasanya menambahkan created_at dan updated_at jika didefinisikan di model
INSERT INTO categories (id, name, description)
VALUES 
(1, 'Elektronik', 'Alat-alat elektronik seperti Laptop, Proyektor, dll.'),
(2, 'Olahraga', 'Alat-alat olahraga seperti Bola, Raket, dll.'),
(3, 'Bengkel', 'Peralatan teknis bengkel.');

-- 2. DATA TOOLS
-- Hapus bagian INSERT users dari seed.sql
-- Biarkan hanya categories dan tools

INSERT INTO tools (category_id, name, description, qr_code, ...)
VALUES 
(1, 'Laptop Asus ROG', 'Core i7, 16GB RAM', UUID(), 5, 5, 'baik', 1, NOW(), NOW()),
(2, 'Proyektor Epson', 'HDMI Support',       UUID(), 3, 3, 'baik', 1, NOW(), NOW()),
(3, 'Bola Basket',     'Original',           UUID(), 10, 10, 'baik', 1, NOW(), NOW());