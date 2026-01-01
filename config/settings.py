from pathlib import Path
import os
from datetime import timedelta
import logging
from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def get_env(name, default=None, required=False):
    value = os.getenv(name, default)
    if required and not value:
        raise ImproperlyConfigured(f"Missing required environment variable: {name}")
    return value


SECRET_KEY = get_env("DJANGO_SECRET_KEY", required=True)
DEBUG = get_env("DJANGO_DEBUG", "0") == "1"

ALLOWED_HOSTS = [h.strip() for h in get_env("DJANGO_ALLOWED_HOSTS", "").split(",") if h.strip()]
if not DEBUG and not ALLOWED_HOSTS:
    raise ImproperlyConfigured("DJANGO_ALLOWED_HOSTS must be set when DEBUG=0")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",

    # Local apps
    "users",
    "core",
    "api",
    "profiles.apps.ProfilesConfig",
    "social",
    "groups",
    "posts",
    "notifications",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DB_ENGINE = get_env("DJANGO_DB_ENGINE", "django.db.backends.sqlite3")
DB_CONN_MAX_AGE = int(get_env("DJANGO_DB_CONN_MAX_AGE", "60"))

if DB_ENGINE == "django.db.backends.sqlite3":
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": DB_ENGINE,
            "NAME": get_env("DJANGO_DB_NAME", required=True),
            "USER": get_env("DJANGO_DB_USER", required=True),
            "PASSWORD": get_env("DJANGO_DB_PASSWORD", required=True),
            "HOST": get_env("DJANGO_DB_HOST", required=True),
            "PORT": get_env("DJANGO_DB_PORT", "5432"),
            "CONN_MAX_AGE": DB_CONN_MAX_AGE,
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "America/New_York"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Custom user model
AUTH_USER_MODEL = "users.User"

# CORS (lock down in prod)
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in get_env("DJANGO_CORS_ALLOWED_ORIGINS", "").split(",") if o.strip()
]
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in get_env("DJANGO_CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]

REDIS_URL = get_env("REDIS_URL", "")
if REDIS_URL:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": REDIS_URL,
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        }
    }
else:
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
            "LOCATION": "default",
        }
    }

# DRF
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "users.authentication.CookieJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticatedOrReadOnly",
    ),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "60/min",
        "user": "600/min",
        "auth_login": "10/min",
        "auth_register": "10/min",
        "user_write": "120/min",
    },
}

ACCESS_MIN = int(get_env("JWT_ACCESS_MINUTES", "15"))
REFRESH_DAYS = int(get_env("JWT_REFRESH_DAYS", "7"))

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=ACCESS_MIN),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=REFRESH_DAYS),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,  # enable with token_blacklist app later
    "UPDATE_LAST_LOGIN": True,
}

JWT_ACCESS_COOKIE_NAME = get_env("JWT_ACCESS_COOKIE_NAME", "access")
JWT_REFRESH_COOKIE_NAME = get_env("JWT_REFRESH_COOKIE_NAME", "refresh")
JWT_COOKIE_SECURE = get_env("JWT_COOKIE_SECURE", "0") == "1" if DEBUG else True
JWT_COOKIE_SAMESITE = get_env("JWT_COOKIE_SAMESITE", "Lax")
JWT_COOKIE_PATH = "/"
CSRF_COOKIE_SAMESITE = get_env("CSRF_COOKIE_SAMESITE", "Lax")
CSRF_COOKIE_SECURE = JWT_COOKIE_SECURE
SESSION_COOKIE_SECURE = JWT_COOKIE_SECURE
SESSION_COOKIE_SAMESITE = JWT_COOKIE_SAMESITE
CSRF_COOKIE_HTTPONLY = get_env("CSRF_COOKIE_HTTPONLY", "0") == "1"

# Security defaults (adjust for prod)
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = get_env("SECURE_SSL_REDIRECT", "1") == "1"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_REFERRER_POLICY = get_env("SECURE_REFERRER_POLICY", "same-origin")
    SECURE_CROSS_ORIGIN_OPENER_POLICY = get_env(
        "SECURE_CROSS_ORIGIN_OPENER_POLICY", "same-origin"
    )
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_BROWSER_XSS_FILTER = True
    X_FRAME_OPTIONS = "DENY"

LOG_LEVEL = get_env("DJANGO_LOG_LEVEL", "INFO")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        }
    },
    "root": {"handlers": ["console"], "level": LOG_LEVEL},
}
