# Feature: Dashboard Analytics API
Fitur ini menyediakan endpoint khusus bagi Admin untuk melihat statistik sistem secara *real-time* dalam satu tampilan.

### Endpoint:
`GET /api/v1/logs/dashboard/stats/`

### Data yang Disajikan:
1.  **Counts**: Total User, Alat, Kategori, dan Transaksi Peminjaman.
2.  **Loans Status**: Jumlah peminjaman yang berstatus `pending`, `approved`, dan `returned`.
3.  **Financial**: Total akumulasi denda yang tercatat dari semua pengembalian.
4.  **Top Tools**: 5 alat yang paling sering dipinjam oleh siswa (beserta jumlahnya).

### Hak Akses:
Hanya user dengan role `admin` yang dapat mengakses endpoint ini.
