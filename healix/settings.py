"""
Django settings for Healix Healthcare Platform
"""
import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

# ── Read .env file manually (no django-environ dependency needed) ──────────────
def get_env(key, default=None):
    """Read from environment or .env file."""
    val = os.environ.get(key)
    if val is not None:
        return val
    env_file = BASE_DIR / '.env'
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    if k.strip() == key:
                        return v.strip()
    return default


SECRET_KEY = get_env('SECRET_KEY', 'healix-insecure-dev-key-change-in-production-min-50-chars!!')
DEBUG = get_env('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

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
    'corsheaders',
    'django_filters',
    'drf_spectacular',

    # Healix apps
    'core.apps.CoreConfig',
    'accounts.apps.AccountsConfig',
    'doctors.apps.DoctorsConfig',
    'appointments.apps.AppointmentsConfig',
    'pharmacies.apps.PharmaciesConfig',
    'prescriptions.apps.PrescriptionsConfig',
    'vitals.apps.VitalsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'healix.urls'
AUTH_USER_MODEL = 'accounts.User'

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

WSGI_APPLICATION = 'healix.wsgi.application'

# ── Database ───────────────────────────────────────────────────────────────────
DATABASE_URL = get_env('DATABASE_URL', '')
if DATABASE_URL.startswith('postgres'):
    import re
    m = re.match(r'postgres(?:ql)?://([^:]+):([^@]+)@([^:/]+):?(\d*)/(.+)', DATABASE_URL)
    if m:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'USER': m.group(1),
                'PASSWORD': m.group(2),
                'HOST': m.group(3),
                'PORT': m.group(4) or '5432',
                'NAME': m.group(5),
            }
        }
    else:
        DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'healix.db'}}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'healix.db',
        }
    }

# ── Auth password validators ───────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Django REST Framework ──────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'healix.pagination.StandardResultsPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'EXCEPTION_HANDLER': 'healix.exceptions.custom_exception_handler',
}

# ── JWT ────────────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'TOKEN_OBTAIN_SERIALIZER': 'accounts.serializers.CustomTokenObtainPairSerializer',
}

# ── CORS ───────────────────────────────────────────────────────────────────────
CORS_ALLOWED_ORIGINS = get_env(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://localhost:8080'
).split(',')
CORS_ALLOW_CREDENTIALS = True

# ── API Docs (Swagger / ReDoc) ─────────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    'TITLE': 'Healix API',
    'DESCRIPTION': (
        'Healix — Healthcare platform connecting patients, doctors, and pharmacies.\n\n'
        '**Authentication:** Use the /api/v1/auth/login/ endpoint to get a Bearer token, '
        'then click "Authorize" and enter: Bearer <your_token>'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'TAGS': [
        {'name': 'Auth', 'description': 'Register, login, logout, token refresh'},
        {'name': 'Patients', 'description': 'Patient medical profile'},
        {'name': 'Doctors', 'description': 'Doctor search, availability, reviews'},
        {'name': 'Appointments', 'description': 'Booking, queue, messaging'},
        {'name': 'Pharmacies', 'description': 'Pharmacy search, medicine inventory'},
        {'name': 'Prescriptions', 'description': 'Prescriptions and scanning'},
    ],
}

# Device
IOT_DEVICE_KEY = get_env('IOT_DEVICE_KEY', 'healix-iot-dev-key-change-in-production')