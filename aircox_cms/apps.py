from django.apps import AppConfig

class AircoxCMSConfig(AppConfig):
    name = 'aircox_cms'
    verbose_name = 'Aircox CMS'

    def ready(self):
        import aircox_cms.signals

