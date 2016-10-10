"""
Sample file for the settings.py

Environment variables:
    * AIRCOX_DEBUG: enable/disable debugging
    * TZ: [in base_settings] timezone (default: 'Europe/Brussels')
    * LANG: [in base_settings] language code

Note that:
    - SECRET_KEY
    - ALLOWED_HOSTS
    - DATABASES

    are not defined in base_settings and must be defined here.

You can also take a look at `base_settings` for more information.

"""
import os
# If Aircox is not installed as a regular python module, you can use:
# import sys
# sys.path.append('/path/to/aircox_parent_folder/')


from .base_settings import *

DEBUG = False
if 'AIRCOX_DEBUG' in os.environ:
    DEBUG = (os.environ['AIRCOX_DEBUG'].lower()) in ('true','1')

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

ALLOWED_HOSTS = ['127.0.0.1:8042']
SECRET_KEY = ''

WAGTAIL_SITE_NAME='Aircox'


