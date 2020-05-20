from django.contrib import admin

from ..models import Port, Station
from .page import NavItemInline


__all__ = ['PortInline', 'StationAdmin']


class PortInline(admin.StackedInline):
    model = Port
    extra = 0


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    inlines = (PortInline, NavItemInline)


