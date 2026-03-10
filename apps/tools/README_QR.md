# Feature: Real-time QR Code Generation
Fitur ini memungkinkan sistem untuk membuat file fisik gambar QR Code (.png) secara otomatis setiap kali User atau Alat (Tool) baru ditambahkan ke database.

### Cara Kerja:
1. Model `User` dan `Tool` meng-override method `save()`.
2. Saat data baru dibuat, sistem memanggil `generate_qr_image` dari `core/utils.py`.
3. File disimpan di folder `media/qrcodes/`.
4. Nama file menggunakan format `user_{username}.png` atau `tool_{8_char_token}.png`.

### Manfaat:
Memudahkan admin untuk mencetak kartu anggota atau label alat secara fisik tanpa perlu men-generate QR secara manual di luar sistem.
