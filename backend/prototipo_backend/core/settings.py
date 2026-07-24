"""
Configurações do projeto EasyRide.

Arquivo de configurações Django para o projeto core.
Utiliza variáveis de ambiente para configurações sensíveis em produção.
"""

import os
from pathlib import Path

import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

# Em produção (DEBUG=False), a SECRET_KEY DEVE ser fornecida via variável de
# ambiente. A ausência levantará KeyError, impedindo o servidor de iniciar
# com uma chave insegura exposta no código-fonte.
if DEBUG:
    SECRET_KEY = os.environ.get(
        'DJANGO_SECRET_KEY',
        'django-insecure-easyride-dev-key-change-in-production',
    )
else:
    SECRET_KEY = os.environ['DJANGO_SECRET_KEY']

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'rest_framework',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
    # Local apps
    'EasyRide.apps.EasyrideConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

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

WSGI_APPLICATION = 'core.wsgi.application'

# Usa DATABASE_URL quando definida (Render injeta automaticamente ao
# provisionar um banco Postgres gerenciado); fallback para SQLite local
# em desenvolvimento.
DATABASES = {
    'default': dj_database_url.config(
        default=f'sqlite:///{BASE_DIR / "db.sqlite3"}',
        conn_max_age=600,
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Cache (conteúdo dinâmico da landing page — Contrato v3.0 §5) ──────
# As rotas /api/beneficios, /api/depoimentos e /api/faq são "rotas
# estáticas (cacheadas)" conforme o contrato. Em desenvolvimento usa-se
# LocMemCache; em produção, DatabaseCache (requer rodar antes
# `python manage.py createcachetable`), já que o plano gratuito do Render
# não oferece Redis.
if os.environ.get('CACHE_BACKEND') == 'database':
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'cache_table',
        }
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

CACHE_TTL_CONTEUDO = int(os.environ.get('CACHE_TTL_CONTEUDO', 900))

# CORS
# Desacoplado de DEBUG: exige variável de ambiente explícita para abrir CORS
# irrestrito, evitando que alguém esqueça DJANGO_DEBUG=False em produção e
# acabe aceitando requisições de qualquer origem sem perceber.
CORS_ALLOW_ALL_ORIGINS = os.environ.get('CORS_ALLOW_ALL_ORIGINS', 'false').lower() in ('true', '1', 'yes')
CORS_ALLOWED_ORIGINS = os.environ.get(
    'CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000'
).split(',')

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DATETIME_FORMAT': 'iso-8601',
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '30/minute',
        'user': '60/minute',
        'leads': '5/minute',
    },
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    # BasicAuthentication primeiro: seu authenticate_header() define o header
    # WWW-Authenticate, o que faz o DRF responder 401 (não 403) a requisições
    # sem credenciais nas rotas protegidas — exigido pelo Contrato v3.0 §7.
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
}

# drf-spectacular — documentação viva da API (GET /api/schema/, /api/docs/)
SPECTACULAR_SETTINGS = {
    'TITLE': 'EasyRide API',
    'VERSION': '3.0',
    'DESCRIPTION': (
        'API do backend EasyRide — captação de leads B2C/B2B, catálogo de '
        'modelos de cadeiras e conteúdo dinâmico da landing page, conforme o '
        'Contrato de Integração da API v3.0.'
    ),
    'SERVE_INCLUDE_SCHEMA': False,
}

# ── Segurança (produção) ──────────────────────────────────────
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
