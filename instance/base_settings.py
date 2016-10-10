import os
import sys
sys.path.insert(1, os.path.dirname(os.path.realpath(__file__)))

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROJECT_ROOT = os.path.normpath(os.path.dirname(__file__) + "/..")

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
SITE_MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')
MEDIA_ROOT = os.path.join(STATIC_ROOT, 'media')

# Internationalization
USE_I18N = True
USE_L10N = True
USE_TZ = True

LANGUAGE_CODE = os.environ.get('LANG') or 'en_US'
TIME_ZONE = os.environ.get('TZ') or 'Europe/Brussels'

try:
    import locale
    locale.setlocale(locale.LC_ALL, LANGUAGE_CODE)
except:
    print(
        'Can not set locale {LC}. Is it available on you system? Hint: '
        'Check /etc/locale.gen and rerun locale-gen as sudo if needed.'
        .format(LC = LANGUAGE_CODE)
    )
    pass

# Application definition
INSTALLED_APPS = (
    'wagtail.wagtailforms',
    'wagtail.wagtailredirects',
    'wagtail.wagtailembeds',
    'wagtail.wagtailsites',
    'wagtail.wagtailusers',
    'wagtail.wagtailsnippets',
    'wagtail.wagtaildocs',
    'wagtail.wagtailimages',
    'wagtail.wagtailsearch',
    'wagtail.wagtailadmin',
    'wagtail.wagtailcore',
    'wagtail.contrib.settings',
    'wagtail.contrib.modeladmin',

    'modelcluster',
    'taggit',
    'honeypot',

    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',

    'aircox',
    'aircox_cms',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.gzip.GZipMiddleware',
    'htmlmin.middleware.HtmlMinifyMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',

    'wagtail.wagtailcore.middleware.SiteMiddleware',
    'wagtail.wagtailredirects.middleware.RedirectMiddleware',
)


ROOT_URLCONF = 'instance.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': (os.path.join(PROJECT_ROOT, 'templates'),),
        # 'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': (
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.request",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",

                'wagtail.contrib.settings.context_processors.settings',
            ),
            'builtins': [
                'overextends.templatetags.overextends_tags'
            ],
            'loaders': (
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ),
        },
    },
]


WSGI_APPLICATION = 'instance.wsgi.application'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'aircox.core': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'aircox.test': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'aircox.tools': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}


# Wagtail
WAGTAIL_SITE_NAME = 'Aircox'


