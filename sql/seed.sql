-- ============================================================
--  APLIKASI PEMINJAMAN ALAT — seed.sql
--  Data awal untuk testing (v1.1.4)
-- ============================================================

USE db_peminjaman_alat;

-- Hapus data lama (Urutan harus benar karena FK)
DELETE FROM activity_logs;
DELETE FROM return_items;
DELETE FROM returns;
DELETE FROM loan_items;
DELETE FROM loans;
DELETE FROM tools;
DELETE FROM categories;
DELETE FROM users;

-- 1. DATA USERS
-- Password default: 'Password123!' (Hash Argon2)
INSERT INTO users (username, email, password, role, is_active, is_staff, is_superuser, qr_token, created_at, updated_at)
VALUES 
('admin', 'admin@sekolah.sch.id', 'argon2$argon2id$v=19$m=65536,t=3,p=4$Z01XUjZ0bHRETVlR$Kz8BqG5H5mYjLzJ3Kz8BqG5H5mYjLzJ3', 'admin', 1, 1, 1, 'uuid_admin_001', NOW(), NOW()),
('petugas1', 'petugas1@sekolah.sch.id', 'argon2$argon2id$v=19$m=65536,t=3,p=4$Z01XUjZ0bHRETVlR$Kz8BqG5H5mYjLzJ3Kz8BqG5H5mYjLzJ3', 'petugas', 1, 1, 0, 'uuid_petugas_001', NOW(), NOW()),
('siswa1', 'siswa1@gmail.com', 'argon2$argon2id$v=19$m=65536,t=3,p=4$Z01XUjZ0bHRETVlR$Kz8BqG5H5mYjLzJ3Kz8BqG5H5mYjLzJ3', 'peminjam', 1, 0, 0, 'uuid_siswa_001', NOW(), NOW());

-- 2. DATA CATEGORIES
INSERT INTO categories (name, description, created_at, updated_at)
VALUES 
('Elektronik', 'Alat-alat elektronik seperti Laptop, Proyektor, dll.', NOW(), NOW()),
('Olahraga', 'Alat-alat olahraga seperti Bola, Raket, dll.', NOW(), NOW()),
('Bengkel', 'Peralatan teknis bengkel.', NOW(), NOW());

-- 3. DATA TOOLS
INSERT INTO tools (category_id, name, description, qr_code, stock_total, stock_available, `condition`, is_active, created_at, updated_at)
VALUES 
(1, 'Laptop Asus ROG', 'Core i7, 16GB RAM', 'tool_asus_001', 5, 5, 'baik', 1, NOW(), NOW()),
(1, 'Proyektor Epson', 'HDMI Support', 'tool_epson_001', 3, 3, 'baik', 1, NOW(), NOW()),
(2, 'Bola Basket Spalding', 'Original', 'tool_basket_001', 10, 10, 'baik', 1, NOW(), NOW());
