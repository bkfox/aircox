![](/data/logo.png)

Platform to manage a radio, schedules, website, and so on. We use the power of great tools like Django or Liquidsoap.

## Current features
* **streams**: multiple random music streams when no program is played. We also can specify a time range and frequency;
* **diffusions**: generate diffusions time slot for programs that have schedule informations. Check for conflicts and rerun.
* **liquidsoap**: create a configuration to use liquidsoap as a stream generator. Also provides interface and control to it;
* **sounds**: each programs have a folder where sounds can be put, that will be detected by the system. Quality can be check and reported for later use. Later, we plan to have uploaders to external plateforms. Sounds can be defined as excerpts or as archives.
* **cms**: application that can be used as basis for website (we use Wagtail; if you don't want it this application is not required to make everything run);
* **log**: keep a trace of every played/loaded sounds on the stream generator.

## Applications
* **programs**: managing stations, programs, schedules and diffusions. This is the core application, that handle most of the work;
* **controllers**: interface with external stream generators. For the moment only support [Liquidsoap](http://liquidsoap.fm/). Generate configuration files, trigger scheduled diffusions and so on;
* **cms**: defines models and templates to generate a website connected to Aircox;

## Installation
### Dependencies
Python modules:
* `django-taggits`: `aircox.programs`, `aircox.cms`
* `watchdog`: `aircox.programs` (used for files monitoring)
* `wagtail`: `aircox.cms`
* `django-honeypot`: `aircox.cms`
* `dateutils`: `aircox.programs` (used for tests)

Applications:
* `liquidsoap`: `aircox.controllers` (generation of the audio streams)

### settings.py
Base configuration:

```python
INSTALLED_APPS = (
    # dependencies
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
    'taggit',
    'honeypot',

    # ...

    # aircox
    'aircox.programs',
    'aircox.controllers',
    'aircox.cms',
)

MIDDLEWARE_CLASSES = (
    # ...
    'wagtail.wagtailcore.middleware.SiteMiddleware',
    'wagtail.wagtailredirects.middleware.RedirectMiddleware',
)

TEMPLATES = [
    {
        # ...
        'OPTIONS': {
            'context_processors': (
                # ...
                'wagtail.contrib.settings.context_processors.settings',
            ),
        },
    },
]

# define your wagtail site name
WAGTAIL_SITE_NAME = 'My Radio'
```

To enable logging:

```python
LOGGING = {
    # ...
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
```

Each application have a `settings.py` that defines options that can be reused in application's `settings.py` file.



