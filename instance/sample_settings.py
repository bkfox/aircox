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
LANGUAGE_CODE = 'en_US'
# locale
LC_LOCALE = 'en_US.UTF-8'
# set current timezone. e.g. 'Europe/Brussels'
TIME_ZONE = os.environ.get('TZ') or 'UTC'

# debug mode
DEBUG = (os.environ['AIRCOX_DEBUG'].lower() in ('true', 1)) \
            if 'AIRCOX_DEBUG' in os.environ else \
        False

if DEBUG:
    from .dev import *
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(PROJECT_ROOT, 'db.sqlite3'),
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
    # caching uses memcache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '127.0.0.1:11211',
        }
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
    locale.setlocale(locale.LC_ALL, LC_LOCALE)
except:
    print(
        'Can not set locale {LC}. Is it available on you system? Hint: '
        'Check /etc/locale.gen and rerun locale-gen as sudo if needed.'
        .format(LC = LANGUAGE_CODE)
    )
    pass


#-- django-ckEditor
CKEDITOR_CONFIGS = {
    "default": {
        "toolbar": "Custom",
        "format_tags": "h1;h2;h3;p;pre",
        "toolbar_Custom": [[
            "Format", "RemoveFormat", "-",
            "Bold", "Italic", "Subscript", "Superscript", "-",
            "NumberedList", "BulletedList", "-",
            "Anchor", "Link", "Unlink", "-",
            "HorizontalRule", "SpecialChar", "-",
            "Source",
        ]],
    },
}
CKEDITOR_CONFIGS["richtext-plugin"] = CKEDITOR_CONFIGS["default"]


#-- easy_thumbnails
THUMBNAIL_PROCESSORS = (
    'easy_thumbnails.processors.colorspace',
    'easy_thumbnails.processors.autocrop',
    #'easy_thumbnails.processors.scale_and_crop',
    'filer.thumbnail_processors.scale_and_crop_with_subject_location',
    'easy_thumbnails.processors.filters',
)


# Application definition
INSTALLED_APPS = (
    'aircox',
    'aircox.apps.AircoxAdminConfig',
    'aircox_streamer',

    # aircox applications
    'rest_framework',
    'django_filters',

    # aircox_web applications
    "content_editor",
    "ckeditor",
    'easy_thumbnails',
    'filer',
    'taggit',
    'adminsortable2',
    'honeypot',

    # django
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.humanize',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
)

MIDDLEWARE = (
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',

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
            ),
            'loaders': (
                'django.template.loaders.filesystem.Loader',
                'django.template.loaders.app_directories.Loader',
            ),
        },
    },
]


WSGI_APPLICATION = 'instance.wsgi.application'

# FIXME: what about dev & prod modules?
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'aircox': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'aircox.commands': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
        'aircox.test': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}


