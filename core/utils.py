# ============================================================
#  core/utils.py — Helper functions yang dipakai banyak modul [v2.0.0]
# ============================================================

import uuid
import qrcode
import io
import base64
import os
from pathlib import Path
from datetime import date
from django.conf import settings
from rest_framework.response import Response
from rest_framework import status


# ------------------------------------------------------------------
# RESPONSE HELPERS
# ------------------------------------------------------------------

def success_response(data=None, message='Berhasil.', status_code=status.HTTP_200_OK):
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
    return str(uuid.uuid4()).replace('-', '')


def generate_qr_image(data: str, filename: str) -> str:
    qr_dir = Path(settings.QR_CODE_DIR)
    qr_dir.mkdir(parents=True, exist_ok=True)

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color='black', back_color='white')
    file_path = qr_dir / f'{filename}.png'
    img.save(file_path)

    return f'qrcodes/{filename}.png'


def generate_qr_user(user) -> str:
    """
    [v2.0.0] Generate QR Card untuk Siswa (Peminjam).
    Simpan ke: media/qrcodes/users/{DEPT}/{KELAS}/qr_{NIS}.png
    """
    dept_kode = user.department.kode if user.department else 'UMUM'
    kelas_sanitized = user.kelas.replace(' ', '_') if user.kelas else 'NO_CLASS'
    nis = user.nis if user.nis else user.username
    
    # Path relative ke MEDIA_ROOT
    relative_path = Path('qrcodes') / 'users' / dept_kode / kelas_sanitized
    full_path = Path(settings.MEDIA_ROOT) / relative_path
    full_path.mkdir(parents=True, exist_ok=True)
    
    filename = f'qr_{nis}.png'
    save_path = full_path / filename
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(user.qr_token)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    img.save(save_path)
    
    return str(relative_path / filename)


def generate_qr_tool(tool) -> str:
    """
    [v2.0.0] Generate QR Label untuk Alat.
    Simpan ke: media/qrcodes/tools/{DEPT}/qr_{nama}.png
    """
    dept_kode = tool.department.kode if tool.department else 'UMUM'
    name_sanitized = tool.name.replace(' ', '_').lower()
    
    relative_path = Path('qrcodes') / 'tools' / dept_kode
    full_path = Path(settings.MEDIA_ROOT) / relative_path
    full_path.mkdir(parents=True, exist_ok=True)
    
    filename = f'qr_{name_sanitized}.png'
    save_path = full_path / filename
    
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(tool.qr_code)
    qr.make(fit=True)
    img = qr.make_image(fill_color='black', back_color='white')
    img.save(save_path)
    
    return str(relative_path / filename)


def qr_to_base64(data: str) -> str:
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
    late_days = (return_date - due_date).days
    if late_days <= 0:
        return {'late_days': 0, 'total_fine': 0.0}
    return {
        'late_days':  late_days,
        'total_fine': late_days * float(fine_per_day),
    }
