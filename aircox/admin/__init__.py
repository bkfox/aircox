from django.contrib import admin


from .episode import DiffusionAdmin, EpisodeAdmin
# from .playlist import PlaylistAdmin
from .program import ProgramAdmin, ScheduleAdmin, StreamAdmin
from .sound import SoundAdmin

from aircox.models import Log, Port, Station


class PortInline(admin.StackedInline):
    model = Port
    extra = 0


@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    inlines = [PortInline]


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ['id', 'date', 'station', 'source', 'type', 'diffusion', 'sound', 'track']
    list_filter = ['date', 'source', 'station']


