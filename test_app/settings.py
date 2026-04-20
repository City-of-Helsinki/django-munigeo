from pathlib import Path

import django.conf.global_settings

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "secret"

DEBUG = True


INSTALLED_APPS = [
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "test_app",
    "munigeo",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "test_app.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "munigeo",
        "USER": "munigeo",
        "PASSWORD": "munigeo",
        "HOST": "localhost",
        "PORT": "5433",
    },
}


USE_TZ = True


STATIC_URL = "static/"

LANGUAGE_CODE = "fi"
language_map = dict(django.conf.global_settings.LANGUAGES)
LANGUAGES = tuple((lang, language_map[lang]) for lang in ["fi", "sv", "en"])
DEFAULT_SRID = 3067
PROJECTION_SRID = 3067

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
