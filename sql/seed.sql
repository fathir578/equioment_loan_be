-- ============================================================
--  APLIKASI PEMINJAMAN ALAT
--  seed.sql — Data awal untuk development & testing
--  Jalankan TERAKHIR setelah semua file SQL lainnya
-- ============================================================

USE db_peminjaman_alat;

-- ------------------------------------------------------------
-- USERS
-- Password semua akun dev = "Password123!"
-- Hash bcrypt di bawah di-generate dari string itu
-- INGAT: Di production, ganti semua password ini!
-- ------------------------------------------------------------
INSERT INTO users (username, email, password, role, qr_token, is_superuser, is_active, is_staff, created_at, updated_at) VALUES
('admin',    'admin@sekolah.sch.id',    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMeSSSmzP0GJxKh.u9Q.QHmZMi', 'admin',    UUID(), 1, 1, 1, NOW(), NOW()),
('petugas1', 'petugas1@sekolah.sch.id', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMeSSSmzP0GJxKh.u9Q.QHmZMi', 'petugas',  UUID(), 0, 1, 1, NOW(), NOW()),
('budi',     'budi@siswa.sch.id',       '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMeSSSmzP0GJxKh.u9Q.QHmZMi', 'peminjam', UUID(), 0, 1, 0, NOW(), NOW()),
('sari',     'sari@siswa.sch.id',       '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMeSSSmzP0GJxKh.u9Q.QHmZMi', 'peminjam', UUID(), 0, 1, 0, NOW(), NOW());

-- ------------------------------------------------------------
-- CATEGORIES
-- ------------------------------------------------------------
INSERT INTO categories (name, description, created_at) VALUES
('Elektronik',  'Peralatan elektronik: laptop, kabel, adaptor, dst', NOW()),
('Mekanik',     'Peralatan mekanik: obeng, tang, kunci pas, dst', NOW()),
('Lab Komputer','Peralatan lab: keyboard, mouse, headset, dst', NOW()),
('Jaringan',    'Peralatan jaringan: switch, kabel UTP, crimping tool, dst', NOW());

-- ------------------------------------------------------------
-- TOOLS
-- ------------------------------------------------------------
INSERT INTO tools (category_id, name, description, qr_code, stock_total, stock_available, `condition`, is_active, created_at, updated_at) VALUES
(1, 'Laptop Lenovo IdeaPad',  '14 inch, RAM 8GB, SSD 256GB', UUID(), 5, 5, 'baik', 1, NOW(), NOW()),
(1, 'Kabel HDMI 2m',          'Kabel HDMI standard',         UUID(), 10, 10, 'baik', 1, NOW(), NOW()),
(2, 'Obeng Set Philips',       'Set obeng Phillips +/-',      UUID(), 8,  8, 'baik', 1, NOW(), NOW()),
(3, 'Keyboard USB',            'Keyboard standar USB',        UUID(), 15, 15, 'baik', 1, NOW(), NOW()),
(3, 'Mouse Wireless',          'Mouse wireless 2.4GHz',       UUID(), 12, 12, 'baik', 1, NOW(), NOW()),
(4, 'Crimping Tool',           'Tang krimping kabel UTP',     UUID(), 6,  6, 'baik', 1, NOW(), NOW()),
(4, 'Kabel UTP Cat6 (per 5m)', 'Kabel UTP category 6',       UUID(), 20, 20, 'baik', 1, NOW(), NOW());
