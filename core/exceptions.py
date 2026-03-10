# ============================================================
#  core/exceptions.py — Format error response yang konsisten
# ============================================================

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Semua error di seluruh aplikasi akan masuk sini.
    Kita bungkus jadi format yang konsisten supaya
    frontend mudah membacanya.

    Format standar error response:
    {
        "success": false,
        "message": "Pesan error yang mudah dibaca manusia",
        "errors": { ... }   ← detail teknis (opsional)
        "status_code": 400
    }
    """
    # Panggil handler bawaan DRF dulu
    response = exception_handler(exc, context)

    if response is not None:
        # Map status code ke pesan yang ramah
        error_messages = {
            400: 'Request tidak valid.',
            401: 'Autentikasi diperlukan. Silakan login.',
            403: 'Anda tidak memiliki izin untuk aksi ini.',
            404: 'Data yang dicari tidak ditemukan.',
            405: 'Method tidak diizinkan.',
            429: 'Terlalu banyak request. Coba lagi sebentar.',
            500: 'Terjadi kesalahan pada server.',
        }

        default_message = error_messages.get(response.status_code, 'Terjadi kesalahan.')

        # Ambil detail error dari response asli
        errors = response.data if isinstance(response.data, dict) else {'detail': response.data}

        # Coba ambil pesan dari field 'detail' jika ada
        message = errors.pop('detail', default_message)
        if hasattr(message, 'code'):
            # TokenExpired, AuthenticationFailed, dll
            message = str(message)

        response.data = {
            'success':     False,
            'message':     message,
            'errors':      errors if errors else None,
            'status_code': response.status_code,
        }

    return response


class BusinessLogicError(Exception):
    """
    Raise ini untuk error logika bisnis (bukan error teknis).
    Contoh: stok habis, loan sudah di-return, dll.
    """
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message     = message
        self.status_code = status_code
        super().__init__(message)
