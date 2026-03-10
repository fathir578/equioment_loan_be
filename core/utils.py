# ============================================================
#  core/utils.py — Helper functions yang dipakai banyak modul
# ============================================================

import uuid
import qrcode
import io
import base64
from pathlib import Path
from datetime import date
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status


# ------------------------------------------------------------------
# RESPONSE HELPERS
# Fungsi ini memastikan format response sukses selalu konsisten
# ------------------------------------------------------------------

def success_response(data=None, message='Berhasil.', status_code=status.HTTP_200_OK):
    """
    Format standar response sukses:
    {
        "success": true,
        "message": "...",
        "data": { ... }
    }
    """
    return Response(
        {'success': True, 'message': message, 'data': data},
        status=status_code
    )


def created_response(data=None, message='Data berhasil dibuat.'):
    return success_response(data, message, status.HTTP_201_CREATED)


# ------------------------------------------------------------------
# QR CODE GENERATOR
# ------------------------------------------------------------------

def generate_qr_token() -> str:
    """
    Generate token unik untuk QR Code.
    UUID4 = 122 bit random → hampir mustahil collision.
    Disimpan di DB sebagai plain string, bukan gambar.
    """
    return str(uuid.uuid4()).replace('-', '')   # 32 karakter hex


def generate_qr_image(data: str, filename: str) -> str:
    """
    Generate gambar QR Code dari string data,
    simpan ke MEDIA_ROOT/qrcodes/, return URL relatif.

    Params:
        data     : string yang di-encode (biasanya token/UUID)
        filename : nama file tanpa ekstensi (contoh: 'user_42')

    Returns:
        URL relatif gambar: 'qrcodes/user_42.png'
    """
    # Pastikan folder ada
    qr_dir = Path(settings.QR_CODE_DIR)
    qr_dir.mkdir(parents=True, exist_ok=True)

    # Buat QR Code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,  # 15% error correction
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color='black', back_color='white')

    # Simpan file
    file_path = qr_dir / f'{filename}.png'
    img.save(file_path)

    return f'qrcodes/{filename}.png'


def qr_to_base64(data: str) -> str:
    """
    Generate QR Code dan return sebagai base64 string.
    Berguna untuk response API tanpa perlu simpan file.
    """
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)

    return base64.b64encode(buffer.read()).decode('utf-8')


# ------------------------------------------------------------------
# DENDA CALCULATOR
# ------------------------------------------------------------------

def calculate_fine(due_date: date, return_date: date, fine_per_day: float) -> dict:
    """
    Hitung keterlambatan dan denda.

    Returns dict:
    {
        'late_days':   5,
        'total_fine':  25000.0
    }
    """
    late_days = (return_date - due_date).days

    if late_days <= 0:
        return {'late_days': 0, 'total_fine': 0.0}

    return {
        'late_days':  late_days,
        'total_fine': late_days * float(fine_per_day),
    }
