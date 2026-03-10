# Feature: Export Reports (CSV)
Fitur ini memungkinkan Admin atau Petugas untuk mengunduh seluruh data peminjaman dalam format file CSV (.csv) yang dapat dibuka menggunakan Microsoft Excel atau Google Sheets.

### Endpoint:
`GET /api/v1/loans/export/csv/`

### Kolom Laporan:
1. **ID**: ID Transaksi Peminjaman.
2. **Peminjam**: Username siswa yang meminjam.
3. **Tanggal Pinjam**: Tanggal awal peminjaman.
4. **Jatuh Tempo**: Tanggal batas pengembalian.
5. **Status**: Status saat ini (`pending`, `approved`, `returned`, dll).
6. **Alat**: Daftar nama alat beserta jumlahnya dalam satu baris.

### Hak Akses:
Hanya user dengan role `admin` atau `petugas` yang dapat mengakses endpoint ini.
