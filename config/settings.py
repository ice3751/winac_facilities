"""
تنظیمات پروژه سامانه مدیریت نهار، ژتون، مهمان و پذیرایی سازمانی (وینک).

تنظیمات حساس از فایل .env خوانده می‌شوند (python-dotenv).
دیتابیس توسعه SQLite است و با تغییر DB_ENGINE در .env به PostgreSQL یا SQL Server
قابل تغییر است.
"""

from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# بارگذاری متغیرهای محیطی از .env (در صورت وجود)
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    return os.getenv(name, str(default)).strip().lower() in {"1", "true", "yes", "on"}


def env_list(name, default=""):
    raw = os.getenv(name, default)
    return [item.strip() for item in raw.split(",") if item.strip()]


# --------------------------------------------------------------------------- #
# امنیت پایه
# --------------------------------------------------------------------------- #
SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-secret-key-change-me")
DEBUG = env_bool("DEBUG", True)
ALLOWED_HOSTS = env_list("ALLOWED_HOSTS", "127.0.0.1,localhost")

# --------------------------------------------------------------------------- #
# اپلیکیشن‌ها
# --------------------------------------------------------------------------- #
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

LOCAL_APPS = [
    "core",
    "accounts",
    "people",
    "guests",
    "meals",
    "catering",
    "attendance",
    "reports",
    "dashboard",
]

INSTALLED_APPS = DJANGO_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # سرو فایل‌های استاتیک در Production بدون نیاز به وب‌سرور جداگانه
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
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
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "core.context_processors.app_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# --------------------------------------------------------------------------- #
# دیتابیس (قابل تعویض از طریق .env)
# --------------------------------------------------------------------------- #
DB_ENGINE = os.getenv("DB_ENGINE", "sqlite").strip().lower()

if DB_ENGINE == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "winac"),
            "USER": os.getenv("DB_USER", ""),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }
elif DB_ENGINE == "mssql":
    # SQL Server از طریق mssql-django + pyodbc
    _mssql_options = {
        "driver": os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server"),
    }
    # برای ODBC Driver 18 معمولاً لازم است: TrustServerCertificate=yes
    _extra = os.getenv("DB_EXTRA_PARAMS", "")
    if _extra:
        _mssql_options["extra_params"] = _extra
    DATABASES = {
        "default": {
            "ENGINE": "mssql",
            "NAME": os.getenv("DB_NAME", "winac"),
            # اگر USER/PASSWORD خالی بماند، احراز هویت ویندوزی (Trusted Connection) استفاده می‌شود
            "USER": os.getenv("DB_USER", ""),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "1433"),
            "OPTIONS": _mssql_options,
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# --------------------------------------------------------------------------- #
# کاربر سفارشی و احراز هویت
# --------------------------------------------------------------------------- #
AUTH_USER_MODEL = "accounts.User"

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "accounts:login"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --------------------------------------------------------------------------- #
# بین‌المللی‌سازی (فارسی / راست‌چین)
# --------------------------------------------------------------------------- #
LANGUAGE_CODE = os.getenv("LANGUAGE_CODE", "fa")
TIME_ZONE = os.getenv("TIME_ZONE", "Asia/Tehran")
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------- #
# فایل‌های استاتیک و رسانه
# --------------------------------------------------------------------------- #
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

# ذخیره‌سازی استاتیک: در Production فشرده و نسخه‌دار توسط WhiteNoise
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage" if DEBUG
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# کلید احراز هویت API داخلی دستگاه تردد (فاز اتصال دستگاه)
DEVICE_API_KEY = os.getenv("DEVICE_API_KEY", "")

# سقف زمانی صدور ژتون نهار (تا ساعت ۱۰ صبح همان روز)
MEAL_TOKEN_CUTOFF_ENABLED = env_bool("MEAL_TOKEN_CUTOFF_ENABLED", True)
MEAL_TOKEN_CUTOFF_HOUR = int(os.getenv("MEAL_TOKEN_CUTOFF_HOUR", "10"))

# --------------------------------------------------------------------------- #
# ایمیل (اطلاع‌رسانی به مدیر اداری و میزبان‌ها)
# --------------------------------------------------------------------------- #
# در توسعه پیش‌فرض console است (ایمیل در ترمینال چاپ می‌شود)؛ در Production مقدار
# EMAIL_BACKEND را به SMTP تغییر دهید.
EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("EMAIL_USE_TLS", True)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "winac-noreply@example.org")
# فعال/غیرفعال‌کردن کلی اطلاع‌رسانی ایمیلی
NOTIFY_EMAIL_ENABLED = env_bool("NOTIFY_EMAIL_ENABLED", True)

# --------------------------------------------------------------------------- #
# امنیت Production (وقتی DEBUG=False فعال می‌شود)
# --------------------------------------------------------------------------- #
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = True
    X_FRAME_OPTIONS = "DENY"
    CSRF_TRUSTED_ORIGINS = env_list("CSRF_TRUSTED_ORIGINS", "")
