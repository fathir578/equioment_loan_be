-- ============================================================
--  SEED DATA: DEPARTMENTS (SMKN 2 SUBANG) [FIXED v2.0.1]
-- ============================================================

INSERT INTO departments (kode, nama, bidang, is_active, created_at) VALUES
('APHP',  'Agribisnis Pengolahan Hasil Pertanian',      'Agribisnis', 1, NOW()),
('APAT',  'Agribisnis Perikanan Air Tawar',              'Agribisnis', 1, NOW()),
('ATPH',  'Agribisnis Tanaman Pangan dan Hortikultura',  'Agribisnis', 1, NOW()),
('ATU',   'Agribisnis Ternak Unggas',                    'Agribisnis', 1, NOW()),
('DPB',   'Desain dan Produksi Busana',                  'Ekonomi dan Seni Kreatif', 1, NOW()),
('TITL',  'Teknik Instalasi Tenaga Listrik',             'Energi dan Pertambangan', 1, NOW()),
('NKN',   'Nautika Kapal Niaga',                         'Kemaritiman', 1, NOW()),
('NKPI',  'Nautika Kapal Penangkap Ikan',                'Kemaritiman', 1, NOW()),
('TKN',   'Teknika Kapal Niaga',                         'Kemaritiman', 1, NOW()),
('KUL',   'Kuliner',                                     'Pariwisata', 1, NOW()),
('ULP',   'Usaha Layanan Pariwisata',                    'Pariwisata', 1, NOW()),
('TAB',   'Teknik Alat Berat',                           'Teknologi Manufaktur dan Rekayasa', 1, NOW()),
('TLOG',  'Teknik Logistik',                             'Teknologi Manufaktur dan Rekayasa', 1, NOW()),
('TPM',   'Teknik Pemesinan',                            'Teknologi Manufaktur dan Rekayasa', 1, NOW()),
('TSM',   'Teknik Sepeda Motor',                         'Teknologi Manufaktur dan Rekayasa', 1, NOW()),
('RPL',   'Rekayasa Perangkat Lunak',                    'Teknologi Informasi', 1, NOW());
