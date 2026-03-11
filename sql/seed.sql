-- ============================================================
--  APLIKASI PEMINJAMAN ALAT — seed.sql
--  Data awal untuk testing (v1.1.5)
-- ============================================================

USE db_peminjaman_alat;

-- 0. Matikan pengecekan Foreign Key agar bisa TRUNCATE/DELETE tanpa error relasi
SET FOREIGN_KEY_CHECKS = 0;

-- Hapus data dari semua tabel terkait (termasuk tabel third-party JWT)
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

-- Reset Auto Increment (Optional tapi bagus untuk seed data)
ALTER TABLE users AUTO_INCREMENT = 1;
ALTER TABLE categories AUTO_INCREMENT = 1;
ALTER TABLE tools AUTO_INCREMENT = 1;
ALTER TABLE loans AUTO_INCREMENT = 1;
ALTER TABLE returns AUTO_INCREMENT = 1;

-- 1. Hidupkan kembali pengecekan Foreign Key
SET FOREIGN_KEY_CHECKS = 1;

-- 2. DATA USERS
-- Password default: 'Password123!' (Hash Argon2)
INSERT INTO users (id, username, email, password, role, is_active, is_staff, is_superuser, qr_token, created_at, updated_at)
VALUES 
(1, 'admin', 'admin@sekolah.sch.id', 'argon2$argon2id$v=19$m=65536,t=3,p=4$Z01XUjZ0bHRETVlR$Kz8BqG5H5mYjLzJ3Kz8BqG5H5mYjLzJ3', 'admin', 1, 1, 1, 'uuid_admin_001', NOW(), NOW()),
(2, 'petugas1', 'petugas1@sekolah.sch.id', 'argon2$argon2id$v=19$m=65536,t=3,p=4$Z01XUjZ0bHRETVlR$Kz8BqG5H5mYjLzJ3Kz8BqG5H5mYjLzJ3', 'petugas', 1, 1, 0, 'uuid_petugas_001', NOW(), NOW()),
(3, 'siswa1', 'siswa1@gmail.com', 'argon2$argon2id$v=19$m=65536,t=3,p=4$Z01XUjZ0bHRETVlR$Kz8BqG5H5mYjLzJ3Kz8BqG5H5mYjLzJ3', 'peminjam', 1, 0, 0, 'uuid_siswa_001', NOW(), NOW());

-- 3. DATA CATEGORIES
INSERT INTO categories (id, name, description, created_at, updated_at)
VALUES 
(1, 'Elektronik', 'Alat-alat elektronik seperti Laptop, Proyektor, dll.', NOW(), NOW()),
(2, 'Olahraga', 'Alat-alat olahraga seperti Bola, Raket, dll.', NOW(), NOW()),
(3, 'Bengkel', 'Peralatan teknis bengkel.', NOW(), NOW());

-- 4. DATA TOOLS
INSERT INTO tools (id, category_id, name, description, qr_code, stock_total, stock_available, `condition`, is_active, created_at, updated_at)
VALUES 
(1, 1, 'Laptop Asus ROG', 'Core i7, 16GB RAM', 'tool_asus_001', 5, 5, 'baik', 1, NOW(), NOW()),
(2, 1, 'Proyektor Epson', 'HDMI Support', 'tool_epson_001', 3, 3, 'baik', 1, NOW(), NOW()),
(3, 2, 'Bola Basket Spalding', 'Original', 'tool_basket_001', 10, 10, 'baik', 1, NOW(), NOW());
