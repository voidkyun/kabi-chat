from pathlib import Path
from urllib.parse import urlparse
import os


BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() in {"1", "true", "yes", "on"}


def env_list(name: str, default: list[str] | None = None) -> list[str]:
    value = os.getenv(name)
    if value is None:
        return default or []
    return [item.strip() for item in value.split(",") if item.strip()]


def database_config() -> dict[str, object]:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("POSTGRES_DB", "kabi_chat"),
            "USER": os.getenv("POSTGRES_USER", "kabi_chat"),
            "PASSWORD": os.getenv("POSTGRES_PASSWORD", "kabi_chat"),
            "HOST": os.getenv("POSTGRES_HOST", "db"),
            "PORT": os.getenv("POSTGRES_PORT", "5432"),
        }

    parsed = urlparse(database_url)
    scheme_to_engine = {
        "postgres": "django.db.backends.postgresql",
        "postgresql": "django.db.backends.postgresql",
    }
    engine = scheme_to_engine.get(parsed.scheme)
    if not engine:
        raise ValueError(f"Unsupported DATABASE_URL scheme: {parsed.scheme}")

    return {
        "ENGINE": engine,
        "NAME": parsed.path.lstrip("/") or os.getenv("POSTGRES_DB", "kabi_chat"),
        "USER": parsed.username or os.getenv("POSTGRES_USER", "kabi_chat"),
        "PASSWORD": parsed.password or os.getenv("POSTGRES_PASSWORD", "kabi_chat"),
        "HOST": parsed.hostname or os.getenv("POSTGRES_HOST", "db"),
        "PORT": str(parsed.port or os.getenv("POSTGRES_PORT", "5432")),
    }


SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "replace-me")
DEBUG = env_bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.auth.apps.AuthConfig",
    "apps.workspaces.apps.WorkspacesConfig",
    "apps.channels.apps.ChannelsConfig",
    "apps.messages.apps.MessagesConfig",
    "apps.macros.apps.MacrosConfig",
]

MIDDLEWARE = [
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
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {"default": database_config()}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "ja-jp"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "Asia/Tokyo")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

JWT_SIGNING_KEY = os.getenv("JWT_SIGNING_KEY", "replace-me")
AUTH_ACCESS_TOKEN_LIFETIME_SECONDS = int(os.getenv("AUTH_ACCESS_TOKEN_LIFETIME_SECONDS", "900"))
AUTH_REFRESH_TOKEN_LIFETIME_DAYS = int(os.getenv("AUTH_REFRESH_TOKEN_LIFETIME_DAYS", "14"))
AUTH_REFRESH_TOKEN_COOKIE_NAME = os.getenv("AUTH_REFRESH_TOKEN_COOKIE_NAME", "kabi_chat_refresh_token")
AUTH_OAUTH_STATE_COOKIE_NAME = os.getenv("AUTH_OAUTH_STATE_COOKIE_NAME", "kabi_chat_oauth_state")
AUTH_OAUTH_STATE_MAX_AGE_SECONDS = int(os.getenv("AUTH_OAUTH_STATE_MAX_AGE_SECONDS", "300"))
AUTH_FRONTEND_CALLBACK_URL = os.getenv("AUTH_FRONTEND_CALLBACK_URL", "")
AUTH_COOKIE_SECURE = env_bool("AUTH_COOKIE_SECURE", default=not DEBUG)
AUTH_COOKIE_SAMESITE = os.getenv("AUTH_COOKIE_SAMESITE", "Lax")
AUTH_COOKIE_DOMAIN = os.getenv("AUTH_COOKIE_DOMAIN") or None
AUTH_COOKIE_PATH = os.getenv("AUTH_COOKIE_PATH", "/")
CSRF_COOKIE_SECURE = env_bool("DJANGO_CSRF_COOKIE_SECURE", default=not DEBUG)
SESSION_COOKIE_SECURE = env_bool("DJANGO_SESSION_COOKIE_SECURE", default=not DEBUG)
SECURE_CONTENT_TYPE_NOSNIFF = env_bool("DJANGO_SECURE_CONTENT_TYPE_NOSNIFF", default=not DEBUG)
SECURE_PROXY_SSL_HEADER = (
    ("HTTP_X_FORWARDED_PROTO", "https")
    if env_bool("DJANGO_USE_PROXY_SSL_HEADER", default=not DEBUG)
    else None
)
USE_X_FORWARDED_HOST = env_bool("DJANGO_USE_X_FORWARDED_HOST", default=not DEBUG)
SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", default=False)
SECURE_HSTS_SECONDS = int(os.getenv("DJANGO_SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool(
    "DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS", default=False
)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_SECURE_HSTS_PRELOAD", default=False)

REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.auth.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
        "rest_framework.authentication.BasicAuthentication",
    ],
}
