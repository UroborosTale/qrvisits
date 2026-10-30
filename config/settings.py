import os
from pathlib import Path
from urllib.parse import urlsplit
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
DEVELOPMENT = os.environ.get('KMZ_ENV') == 'development'
DEBUG = DEVELOPMENT
SECRET_KEY = os.environ.get('SECRET_KEY', '')
if not SECRET_KEY:
    if not DEVELOPMENT:
        raise ImproperlyConfigured('Set SECRET_KEY for production.')
    SECRET_KEY = 'local-development-only-not-a-production-secret'
if not DEVELOPMENT and (len(SECRET_KEY) < 50 or 'CHANGE_ME' in SECRET_KEY):
    raise ImproperlyConfigured('Generate a unique SECRET_KEY of at least 50 characters.')
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1' if DEVELOPMENT else '').split(',')
PUBLIC_BASE_URL = os.environ.get('PUBLIC_BASE_URL', 'http://127.0.0.1:8000' if DEVELOPMENT else '').rstrip('/')
parsed = urlsplit(PUBLIC_BASE_URL)
if (parsed.scheme not in ('http', 'https') or not parsed.netloc or parsed.path
        or parsed.query or parsed.fragment or parsed.username or parsed.password):
    raise ImproperlyConfigured('PUBLIC_BASE_URL must be an absolute origin without a path.')
if not DEVELOPMENT and (parsed.scheme != 'https' or not any(ALLOWED_HOSTS) or '*' in ALLOWED_HOSTS):
    raise ImproperlyConfigured('Production requires HTTPS PUBLIC_BASE_URL and explicit ALLOWED_HOSTS.')
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles', 'cards',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware', 'cards.middleware.LocalPreviewOriginMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', 'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware', 'cards.middleware.PrivacyHeadersMiddleware',
]
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [], 'APP_DIRS': True,
    'OPTIONS': {'context_processors': ['django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages']},
}]
WSGI_APPLICATION = 'config.wsgi.application'
if os.environ.get('POSTGRES_HOST'):
    if not DEVELOPMENT and (not os.environ.get('POSTGRES_PASSWORD') or 'CHANGE_ME' in os.environ['POSTGRES_PASSWORD']):
        raise ImproperlyConfigured('Set a unique database password.')
    DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql',
        'HOST': os.environ['POSTGRES_HOST'], 'PORT': os.environ.get('POSTGRES_PORT', '5432'),
        'NAME': os.environ.get('POSTGRES_DB', 'kmz'), 'USER': os.environ.get('POSTGRES_USER', 'kmz'),
        'PASSWORD': os.environ['POSTGRES_PASSWORD'], 'CONN_MAX_AGE': 60}}
else:
    if not DEVELOPMENT:
        raise ImproperlyConfigured('Production requires PostgreSQL.')
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': BASE_DIR / 'db.sqlite3'}}
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 12}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'ru'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/private-media/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
DATA_UPLOAD_MAX_MEMORY_SIZE = 6 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 8 * 60 * 60
SESSION_COOKIE_SECURE = not DEVELOPMENT
CSRF_COOKIE_SECURE = not DEVELOPMENT
SECURE_SSL_REDIRECT = not DEVELOPMENT
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
CSRF_TRUSTED_ORIGINS = [PUBLIC_BASE_URL]
SECURE_HSTS_SECONDS = 31536000 if not DEVELOPMENT else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'no-referrer'
X_FRAME_OPTIONS = 'DENY'
COMPANY_NAME = 'Карачаровский механический завод'
COMPANY_WEBSITE = 'https://www.kmzlift.ru'
