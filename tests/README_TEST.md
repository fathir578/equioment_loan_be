# Feature: Automated Testing
Fitur ini menyediakan skrip pengujian otomatis untuk memastikan logika bisnis yang krusial tetap berjalan dengan benar meskipun terjadi perubahan kode di masa depan.

### Cara Menjalankan Test:
`python manage.py test tests/`

### Kasus Uji yang Dicakup:
1.  **test_stock_decrease_on_approve**: Memastikan bahwa saat sebuah peminjaman disetujui (approved), stok alat di database berkurang secara otomatis melalui trigger SQL.
2.  **test_fine_calculation**: Memastikan bahwa Stored Procedure `sp_process_return` menghitung denda dengan benar berdasarkan selisih hari antara tanggal jatuh tempo dan tanggal pengembalian.

### Teknologi:
Menggunakan `django.test.TransactionTestCase` karena pengujian ini melibatkan pemanggilan *Stored Procedures* dan *Triggers* yang memerlukan commit transaksi secara nyata di dalam sesi test.
