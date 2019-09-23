from django.contrib import admin

from ..models import Station
from .page import NavItemInline


__all__ = ['StationAdmin']


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    inlines = (NavItemInline,)


