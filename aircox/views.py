import os
import json
import datetime

from django.views.generic.base import View, TemplateResponseMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.utils.translation import ugettext as _
from django.utils import timezone as tz
from django.views.decorators.cache import cache_page

import aircox.models as models


# FIXME usefull?
class Stations:
    stations = models.Station.objects.all()
    update_timeout = None
    fetch_timeout = None

    def fetch(self):
        if self.fetch_timeout and self.fetch_timeout > tz.now():
            return

        self.fetch_timeout = tz.now() + tz.timedelta(seconds=5)
        for station in self.stations:
            station.streamer.fetch()


stations = Stations()


@cache_page(10)
def on_air(request):
    try:
        import aircox_cms.models as cms
    except:
        cms = None

    station = request.GET.get('station')
    if station:
        # FIXME: by name???
        station = stations.stations.filter(name=station)
        if not station.count():
            return HttpResponse('{}')
    else:
        station = stations.stations

    station = station.first()
    on_air = station.on_air(count=10).select_related('track', 'diffusion')
    if not on_air.count():
        return HttpResponse('')

    last = on_air.first()
    if last.track:
        last = {'date': last.date, 'type': 'track',
                'artist': last.track.artist, 'title': last.track.title}
    else:
        try:
            diff = last.diffusion
            publication = None
            # FIXME CMS
            if cms:
                publication = \
                    cms.DiffusionPage.objects.filter(
                        diffusion=diff.initial or diff).first() or \
                    cms.ProgramPage.objects.filter(
                        program=last.program).first()
        except:
            pass
        last = {'date': diff.start, 'type': 'diffusion',
                'title': diff.program.name,
                'url': publication.specific.url if publication else None}
    last['date'] = str(last['date'])
    return HttpResponse(json.dumps(last))


# TODO:
#   - login url
class Monitor(View, TemplateResponseMixin, LoginRequiredMixin):
    template_name = 'aircox/controllers/monitor.html'

    def get_context_data(self, **kwargs):
        stations.fetch()
        return {'stations': stations.stations}

    def get(self, request=None, **kwargs):
        if not request.user.is_active:
            return Http404()

        self.request = request
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)

    def post(self, request=None, **kwargs):
        if not request.user.is_active:
            return Http404()

        if not ('action' or 'station') in request.POST:
            return HttpResponse('')

        POST = request.POST
        POST.get('controller')
        action = POST.get('action')

        station = stations.stations.filter(name=POST.get('station')) \
                                   .first()
        if not station:
            return Http404()

        source = None
        if 'source' in POST:
            source = [s for s in station.sources
                      if s.name == POST['source']]
            source = source[0]
            if not source:
                return Http404

        station.streamer.fetch()
        source = source or station.streamer.source
        if action == 'skip':
            self.actionSkip(request, station, source)
        if action == 'restart':
            self.actionRestart(request, station, source)
        return HttpResponse('')

    def actionSkip(self, request, station, source):
        source.skip()

    def actionRestart(self, request, station, source):
        source.restart()


class StatisticsView(View, TemplateResponseMixin, LoginRequiredMixin):
    """
    View for statistics.
    """
    # we cannot manipulate queryset: we have to be able to read from archives
    template_name = 'aircox/controllers/stats.html'

    class Item:
        date = None
        end = None
        name = None
        related = None
        tracks = None
        tags = None
        col = None

        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class Stats:
        station = None
        date = None
        items = None
        """
        Log or Diffusion object that has been diffused by date. These
        objects have extra fields:
            - tags: [ (tag_name, tag_count), ...]
            - tracks_count: total count of tracks
        """
        count = 0
        #rows = None

        def __init__(self, **kwargs):
            self.items = []
        #    self.rows = []
            self.__dict__.update(kwargs)

        # Note: one row contains a column for diffusions and one for streams
        # def append(self, log):
        #    if log.col == 0:
        #        self.rows.append((log, []))
        #        return
        #
        #    if self.rows:
        #        row = self.rows[len(self.rows)-1]
        #        last = row[0] or row[1][len(row[1])-1]
        #        if last.date < log.date < last.end:
        #            row[1].append(log)
        #            return
        #
        #    # all other cases: new row
        #    self.rows.append((None, [log]))

    def get_stats(self, station, date):
        """
        Return statistics for the given station and date.
        """
        stats = self.Stats(station=station, date=date,
                           items=[], tags={})

        qs = Log.objects.station(station).on_air() \
                .prefetch_related('diffusion', 'sound', 'track', 'track__tags')
        if not qs.exists():
            qs = models.Log.objects.load_archive(station, date)

        sound_log = None
        for log in qs:
            rel, item = None, None
            if log.diffusion:
                rel, item = log.diffusion, self.Item(
                    name=rel.program.name, type=_('Diffusion'), col=0,
                    tracks=models.Track.objects.filter(diffusion=log.diffusion)
                                       .prefetch_related('tags'),
                )
                sound_log = None
            elif log.sound:
                rel, item = log.sound, self.Item(
                    name=rel.program.name + ': ' + os.path.basename(rel.path),
                    type=_('Stream'), col=1, tracks=[],
                )
                sound_log = item
            elif log.track:
                # append to last sound log
                if not sound_log:
                    continue
                sound_log.tracks.append(log.track)
                sound_log.end = log.end
                continue

            item.date = log.date
            item.end = log.end
            item.related = rel
            # stats.append(item)
            stats.items.append(item)
        return stats

    def get_context_data(self, **kwargs):
        context = {}
        date = datetime.date.today()

        try:
            GET = self.request.GET
            year = int(GET["year"]) if 'year' in GET else date.year
            month = int(GET["month"]) if 'month' in GET else date.month
            day = int(GET["day"]) if 'day' in GET else date.day
            date = datetime.date(year, month, day)
        except:
            pass

        context["statistics"] = [
            self.get_stats(station, date)
            for station in models.Station.objects.all()
        ]

        return context

    def get(self, request=None, **kwargs):
        if not request.user.is_active:
            return Http404()

        self.request = request
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)
