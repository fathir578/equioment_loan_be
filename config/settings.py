# ============================================================
#  config/settings.py — Konfigurasi utama Django
# ============================================================

import environ
from pathlib import Path
from datetime import timedelta

# Base directory project
BASE_DIR = Path(__file__).resolve().parent.parent

# Baca file .env
env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / '.env')

# ------------------------------------------------------------------
# SECURITY
# ------------------------------------------------------------------
SECRET_KEY = env('SECRET_KEY')
DEBUG = env('DEBUG')
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1'])

# ------------------------------------------------------------------
# APPLICATIONS
# ------------------------------------------------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'drf_spectacular',
    'corsheaders',

    # Local apps
    'apps.users',
    'apps.categories',
    'apps.tools',
    'apps.loans',
    'apps.returns',
    'apps.activity_logs',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',        # CORS — harus di atas CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'core.middleware.ActivityLogMiddleware',        # Custom: auto-log setiap request
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# ------------------------------------------------------------------
# DATABASE — MySQL
# ------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME':   env('DB_NAME'),
        'USER':   env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST':   env('DB_HOST', default='localhost'),
        'PORT':   env('DB_PORT', default='3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# ------------------------------------------------------------------
# AUTH — Gunakan model User custom kita
# ------------------------------------------------------------------
AUTH_USER_MODEL = 'users.User'

# ------------------------------------------------------------------
# DJANGO REST FRAMEWORK
# ------------------------------------------------------------------
REST_FRAMEWORK = {
    # Default: semua endpoint butuh login
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    # Pagination default untuk semua endpoint list
    'DEFAULT_PAGINATION_CLASS': 'core.pagination.StandardPagination',
    'PAGE_SIZE': 10,

    # Filter & search
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],

    # Throttling / Rate Limiting
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '20/minute',      # User belum login: 20 req/menit
        'user': '100/minute',     # User sudah login: 100 req/menit
        'login': '5/minute',      # Khusus endpoint login: 5 req/menit (anti brute-force)
    },

    # Format error yang konsisten
    'EXCEPTION_HANDLER': 'core.exceptions.custom_exception_handler',

    # Auto docs
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# ------------------------------------------------------------------
# JWT SETTINGS
# ------------------------------------------------------------------
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME':  timedelta(minutes=env.int('JWT_ACCESS_TOKEN_LIFETIME_MINUTES', default=60)),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=env.int('JWT_REFRESH_TOKEN_LIFETIME_DAYS', default=7)),
    'ROTATE_REFRESH_TOKENS':  True,    # Setiap refresh, token baru dikeluarkan
    'BLACKLIST_AFTER_ROTATION': True,  # Token lama langsung di-blacklist
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# ------------------------------------------------------------------
# DRF SPECTACULAR (Auto Swagger Docs)
# ------------------------------------------------------------------
SPECTACULAR_SETTINGS = {
    'TITLE': 'API Peminjaman Alat',
    'DESCRIPTION': 'REST API untuk sistem peminjaman alat sekolah — UKK RPL 2025/2026',
    'VERSION': '0.1.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

# ------------------------------------------------------------------
# CORS
# ------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# ------------------------------------------------------------------
# MEDIA & STATIC (untuk file QR Code)
# ------------------------------------------------------------------
STATIC_URL  = '/static/'
MEDIA_URL   = '/media/'
MEDIA_ROOT  = BASE_DIR / 'media'
QR_CODE_DIR = BASE_DIR / env('QR_CODE_DIR', default='media/qrcodes')

# ------------------------------------------------------------------
# BUSINESS LOGIC SETTINGS
# ------------------------------------------------------------------
DEFAULT_FINE_PER_DAY = env.int('DEFAULT_FINE_PER_DAY', default=5000)

# ------------------------------------------------------------------
# TEMPLATES (untuk Django Admin)
# ------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ------------------------------------------------------------------
# INTERNATIONALIZATION
# ------------------------------------------------------------------
LANGUAGE_CODE = 'id'          # Bahasa Indonesia
TIME_ZONE     = 'Asia/Jakarta'
USE_I18N      = True
USE_TZ        = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
