from django.apps import AppConfig
from django.contrib.admin.apps import AdminConfig


class AircoxConfig(AppConfig):
    name = 'aircox'
    verbose_name = 'Aircox'


class AircoxAdminConfig(AdminConfig):
    default_site = 'aircox.views.admin.AdminSite'



