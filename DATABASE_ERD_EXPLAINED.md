# Penjelasan Struktur Database & ERD
**Proyek:** Sistem Peminjaman Alat Sekolah
**Status:** Dokumen Rahasia (Hanya untuk Developer)

---

## 1. Rincian Tabel & Kolom

### 1.1 Tabel `users`
Menyimpan identitas semua pengguna sistem.
*   `id`: Primary Key (Auto Increment).
*   `username`: Unik, identitas login.
*   `email`: Unik, alamat surel.
*   `password`: Hash (Bcrypt/PBKDF2).
*   `role`: Enum ('admin', 'petugas', 'peminjam').
*   `qr_token`: Unik, token rahasia untuk kartu QR.
*   `is_active`, `is_staff`: Flag keamanan Django.

### 1.2 Tabel `categories`
Klasifikasi alat.
*   `id`: Primary Key.
*   `name`: Nama kategori (Unik).
*   `description`: Deskripsi singkat.

### 1.3 Tabel `tools` (Alat)
Katalog fisik alat.
*   `id`: Primary Key.
*   `category_id`: Foreign Key ke `categories`.
*   `name`: Nama alat.
*   `stock_total`: Stok awal pengadaan.
*   `stock_available`: Stok yang bisa dipinjam saat ini.
*   `condition`: Enum ('baik', 'rusak_ringan', 'rusak_berat').
*   `qr_code`: Token fisik yang tertempel di alat.

### 1.4 Tabel `loans` (Header Peminjaman)
Mencatat siapa yang meminjam dan kapan.
*   `id`: Primary Key.
*   `user_id`: FK ke `users` (Si Peminjam).
*   `approved_by`: FK ke `users` (Petugas yang approve).
*   `loan_date`: Tanggal pinjam.
*   `due_date`: Tanggal jatuh tempo kembali.
*   `status`: Enum ('pending', 'approved', 'rejected', 'partial_returned', 'returned').

### 1.5 Tabel `loan_items` (Detail Peminjaman)
*   `id`: Primary Key.
*   `loan_id`: FK ke `loans`.
*   `tool_id`: FK ke `tools`.
*   `quantity`: Jumlah alat yang dipinjam.
*   `quantity_returned`: Melacak berapa yang sudah kembali (untuk partial return).

### 1.6 Tabel `returns` (Sesi Pengembalian)
Setiap kali siswa datang membawa alat, dicatat satu sesi ini.
*   `id`: Primary Key.
*   `loan_id`: FK ke `loans`.
*   `processed_by`: FK ke `users` (Petugas penerima).
*   `return_date`: Tanggal aktual kembali.
*   `late_days`: Jumlah hari terlambat (otomatis dari SP).
*   `total_fine`: Total denda sesi ini (otomatis dari SP).

### 1.7 Tabel `return_items` (Detail Kembalian)
*   `id`: Primary Key.
*   `return_id`: FK ke `returns`.
*   `loan_item_id`: FK ke `loan_items`.
*   `quantity_returned`: Jumlah yang dikembalikan saat ini.
*   `condition_on_return`: Kondisi alat saat diterima kembali.

### 1.8 Tabel `activity_logs`
*   `id`: Primary Key.
*   `user_id`: FK ke `users` (Opsional).
*   `action`: Nama aksi (misal: "POST /loans/").
*   `ip_address`: Alamat IP pengakses.

---

## 2. Logika Relasi Penting

1.  **Partial Return Support:** Satu `Loan` bisa memiliki banyak `Returns`. Contoh: Pinjam 10 kursi, hari ini kembali 5 (Return #1), besok kembali 5 (Return #2). Itulah kenapa ada tabel `return_items` yang merujuk ke `loan_items`.
2.  **Double FK to Users:** Tabel `loans` punya dua relasi ke user: satu sebagai subjek (peminjam) dan satu sebagai objek otoritas (approver).
3.  **Audit Trail:** `activity_logs` didesain dengan `ON DELETE SET NULL`. Artinya jika user dihapus, catatan riwayatnya tetap ada (audit trail tidak boleh hilang).

---

## 3. Keamanan Level Database

*   **Trigger `trg_validate_loan_approver`**: Mencegah kecurangan. Peminjam tidak bisa menyetujui pinjamannya sendiri meskipun dia punya akses ke database.
*   **Check Constraint**: `stock_available` tidak akan pernah bisa lebih besar dari `stock_total`.
*   **SP Transaction**: Seluruh proses peminjaman berada dalam satu transaksi. Jika salah satu alat gagal di-lock stoknya, maka seluruh peminjaman batal (tidak ada data menggantung).
