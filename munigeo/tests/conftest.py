import django
from django.conf import settings

CUSTOM_INSTALLED_APPS = (
    'munigeo',
)

ALWAYS_INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

ALWAYS_MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)
settings.configure(
    DATABASES={
        'default': {
            'ENGINE': 'django.contrib.gis.db.backends.postgis',
            'NAME': 'servicemap-api',
            'ATOMIC_REQUESTS': True,
        }
    },
    SECRET_KEY="django_tests_secret_key",
    DEBUG=False,
    TEMPLATE_DEBUG=False,
    ALLOWED_HOSTS=[],
    INSTALLED_APPS=ALWAYS_INSTALLED_APPS + CUSTOM_INSTALLED_APPS,
    MIDDLEWARE_CLASSES=ALWAYS_MIDDLEWARE_CLASSES,
    LANGUAGE_CODE='en-us',
    TIME_ZONE='UTC',
    USE_I18N=True,
    USE_L10N=True,
    USE_TZ=True,
    STATIC_URL='/static/',
)

django.setup()
