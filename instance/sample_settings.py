"""
Sample file for the settings.py

First part of the file is where you should put your hand, second part is
just basic django initialization.


Some variable retrieve environnement variable if they are defined:
    * AIRCOX_DEBUG: enable/disable debugging
    * TZ: timezone (default: 'Europe/Brussels')
    * LANG: language code

Note that:
    - SECRET_KEY
    - ALLOWED_HOSTS
    - DATABASES

    are not defined in sample_settings and must be defined here.

You can also configure specific Aircox & Aircox CMS settings. For more
information, please report to these application's settings.py

For Django settings see:
    https://docs.djangoproject.com/en/1.8/topics/settings/
    https://docs.djangoproject.com/en/1.8/ref/settings/
"""
import os
import sys
import pytz

from django.utils import timezone

sys.path.insert(1, os.path.dirname(os.path.realpath(__file__)))

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
STATIC_URL = '/static/'
MEDIA_URL = '/media/'
SITE_MEDIA_URL = '/media/'
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')
MEDIA_ROOT = os.path.join(STATIC_ROOT, 'media')


########################################################################
#
# You can configure starting from here
#
########################################################################

# set current language code. e.g. 'fr_BE'
LANGUAGE_CODE = os.environ.get('LANG') or 'en_US'
# set current timezone. e.g. 'Europe/Brussels'
TIME_ZONE = os.environ.get('TZ') or 'UTC'

# wagtail site name
WAGTAIL_SITE_NAME = 'Aircox'

# debug mode
DEBUG = (os.environ['AIRCOX_DEBUG'].lower() in ('true', 1)) \
            if 'AIRCOX_DEBUG' in os.environ else \
        False

if DEBUG:
    from .dev import *
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
            'TIMEZONE': TIME_ZONE,
        }
    }
else:
    from .prod import *
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'aircox',
            'USER': 'aircox',
            'PASSWORD': '',
            'HOST': 'localhost',
            'TIMEZONE': TIME_ZONE,
        },
    }

# allowed hosts
ALLOWED_HOSTS = ('127.0.0.1',)

# secret key: you MUST put a consistent secret key
SECRET_KEY = ''


########################################################################
#
# You don't really need to configure what is happening below
#
########################################################################
# Internationalization and timezone
USE_I18N = True
USE_L10N = True
USE_TZ = True

timezone.activate(pytz.timezone(TIME_ZONE))

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
    'aircox',
    'aircox_cms',

    'jet',
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
)

MIDDLEWARE = (
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

    'aircox.middleware.AircoxMiddleware'
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


