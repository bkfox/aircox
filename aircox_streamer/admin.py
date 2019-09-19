from django.contrib import admin

from aircox.admin import StationAdmin
from .models import Port


__all__ = ['PortInline']


class PortInline(admin.StackedInline):
    model = Port
    extra = 0


StationAdmin.inlines = (PortInline,) + StationAdmin.inlines


