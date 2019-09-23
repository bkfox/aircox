from django.contrib import admin

from ..models import Log


__all__ = ['LogAdmin']


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'station', 'source', 'type', 'comment']
    list_filter = ['date', 'source', 'station']

