#!/usr/bin/env python
"""
Django's command-line utility untuk administrative tasks.
Cara pakai:
    python manage.py runserver          → jalankan dev server
    python manage.py makemigrations     → buat file migrasi
    python manage.py migrate            → jalankan migrasi ke DB
    python manage.py createsuperuser    → buat akun admin
    python manage.py shell              → Django interactive shell
"""
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Tidak bisa import Django. Pastikan sudah install: pip install -r requirements.txt"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
