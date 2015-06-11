from django.conf import settings

def ensure (key, default):
    globals()[key] = getattr(settings, key, default)


ensure('AIRCOX_PROGRAMS_DATA', settings.MEDIA_ROOT + '/programs')



