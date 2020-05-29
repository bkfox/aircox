"""
Django and Aircox instance settings. This file should be saved as `settings.py`
in the same directory as this one.

User MUST define the following values: `SECRET_KEY`, `ALLOWED_HOSTS`, `DATABASES`

The following environment variables are used in settings:
    * `AIRCOX_DEBUG` (`DEBUG`): enable/disable debugging

For Django settings see:
    https://docs.djangoproject.com/en/3.1/topics/settings/
    https://docs.djangoproject.com/en/3.1/ref/settings/

"""
import os
import sys
import pytz
from django.utils import timezone

sys.path.insert(1, os.path.dirname(os.path.realpath(__file__)))

# Project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
# DEBUG mode
DEBUG = (os.environ['AIRCOX_DEBUG'].lower() in ('true', 1)) \
            if 'AIRCOX_DEBUG' in os.environ else \
        False

# Internationalization and timezones: thoses values may be set in order to
# have correct translation and timezone.

# Current language code. e.g. 'fr_BE'
LANGUAGE_CODE = 'en-US'
# Locale
LC_LOCALE = 'en_US.UTF-8'
# Current timezone. e.g. 'Europe/Brussels'
TIME_ZONE = os.environ.get('TZ') or 'UTC'


########################################################################
#
# You MUST configure those values
#
########################################################################

# Secret key: you MUST put a consistent secret key. You can generate one
# at https://djecrety.ir/
SECRET_KEY = ''

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PROJECT_ROOT, 'db.sqlite3'),
        'TIMEZONE': TIME_ZONE,
    }
}

# Allowed host for HTTP requests
ALLOWED_HOSTS = ('127.0.0.1',)

########################################################################
#
# You CAN configure starting from here
#
########################################################################

# Assets and medias:
# In production, user MUST configure webserver in order to serve static
# and media files.

# Website's path to statics assets
STATIC_URL = '/static/'
# Website's path to medias (uploaded images, etc.)
MEDIA_URL = '/media/'
# Website URL path to medias (uploaded images, etc.)
SITE_MEDIA_URL = '/media/'
# Path to assets' directory (by default in project's directory)
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')
# Path to media directory (by default in static's directory)
MEDIA_ROOT = os.path.join(STATIC_ROOT, 'media')

# Include specific configuration depending of DEBUG
if DEBUG:
    from .dev import *
else:
    from .prod import *

    # Enable caching using memcache
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
            'LOCATION': '127.0.0.1:11211',
        }
    }


########################################################################
#
# You don't really need to configure what is happening below
#
########################################################################
# Enables internationalization and timezone
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


#-- django-CKEditor
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


# Enabled applications
INSTALLED_APPS = (
    'aircox',
    'aircox.apps.AircoxAdminConfig',
    'aircox_streamer',

    # Aircox dependencies
    'rest_framework',
    'django_filters',
    "content_editor",
    "ckeditor",
    'easy_thumbnails',
    'filer',
    'taggit',
    'adminsortable2',
    'honeypot',

    # Django
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

