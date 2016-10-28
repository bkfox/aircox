import json
import datetime

from django.db.models import Count
from django.views.generic.base import View, TemplateResponseMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils import timezone as tz

import aircox.models as models


class Stations:
    stations = models.Station.objects.all()
    update_timeout = None
    fetch_timeout = None

    def fetch(self):
        if self.fetch_timeout and self.fetch_timeout > tz.now():
            return

        self.fetch_timeout = tz.now() + tz.timedelta(seconds = 5)
        for station in self.stations:
            station.streamer.fetch()

stations = Stations()


def on_air(request):
    try:
        import aircox_cms.models as cms
    except:
        cms = None

    station = request.GET.get('station');
    if station:
        station = stations.stations.filter(name = station)
    else:
        station = stations.stations.first()

    last = station.on_air(count = 1)
    if not last:
        return HttpResponse('')

    last = last[0]
    if type(last) == models.Log:
        last = {
            'type': 'track',
            'artist': last.related.artist,
            'title': last.related.title,
            'date': last.date,
        }
    else:
        try:
            publication = None
            if cms:
                publication = \
                    cms.DiffusionPage.objects.filter(
                        diffusion = last.initial or last).first() or \
                    cms.ProgramPage.objects.filter(
                        program = last.program).first()
        except:
            pass

        last = {
            'type': 'diffusion',
            'title': last.program.name,
            'date': last.start,
            'url': publication.specific.url if publication else None,
        }

    last['date'] = str(last['date'])
    return HttpResponse(json.dumps(last))


# TODO:
#   - login url
class Monitor(View,TemplateResponseMixin,LoginRequiredMixin):
    template_name = 'aircox/controllers/monitor.html'

    def get_context_data(self, **kwargs):
        stations.fetch()
        return { 'stations': stations.stations }

    def get(self, request = None, **kwargs):
        if not request.user.is_active:
            return Http404()

        self.request = request
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)

    def post(self, request = None, **kwargs):
        if not request.user.is_active:
            return Http404()

        if not ('action' or 'station') in request.POST:
            return HttpResponse('')

        POST = request.POST
        controller = POST.get('controller')
        action = POST.get('action')

        station = stations.stations.filter(name = POST.get('station')) \
                                   .first()
        if not station:
            return HttpResponse('')
        station.prepare(fetch=True)

        source = None
        if 'source' in POST:
            source = next([ s for s in station.sources
                                if s.name == POST['source']], None)

        if station and action == 'skip':
            if source:
                source.skip()
            else:
                station.streamer.skip()

        return HttpResponse('')


class StatisticsView(View,TemplateResponseMixin,LoginRequiredMixin):
    template_name = 'aircox/controllers/stats.html'

    class Taggable:
        tags = None

        def add_tags(self, qs):
            if not self.tags:
                self.tags = {}

            qs = qs.values('tags__name').annotate(count = Count('tags__name')) \
                    .order_by('tags__name')
            for q in qs:
                key = q['tags__name']
                if not key:
                    continue

                value = q['count']
                if key not in self.tags:
                    self.tags[key] = value
                else:
                    self.tags[key] += value

    class Item (Taggable):
        type = ''
        date = None
        name = None
        related = None
        tracks = None
        tags = None

        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)

    class Stats (Taggable):
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

        def __init__(self, **kwargs):
            self.items = []
            self.__dict__.update(kwargs)

    def get_stats(self, station, date):
        """
        Return statistics for the given station and date.
        """
        stats = self.Stats(station = station, date = date,
                           items = [], tags = {})

        last_item = None
        for elm in reversed(station.on_air(date)):
            qs = None
            item = None
            if type(elm) == models.Diffusion:
                qs = models.Track.objects.get_for(elm)
                item = self.Item(
                    type = _('Diffusion'),
                    date = elm.date,
                    name = elm.program.name,
                    related = elm,
                    tracks = qs[:]
                )
                item.add_tags(qs)
                stats.items.append(item)
                stats.count += len(item.tracks)

            else:
                # type is Track (related object of a track is a sound)
                stream = elm.related.related
                qs = models.Track.objects.filter(pk = elm.related.pk)

                if last_item and last_item.related == stream:
                    item = last_item
                else:
                    item = self.Item(
                        type = _('Stream'),
                        date = elm.date,
                        name = stream.path,
                        related = stream,
                        tracks = []
                    )
                    stats.items.append(item)

                elm.related.date = elm.date
                item.tracks.append(elm.related)
                item.date = min(elm.date, item.date)
                item.add_tags(qs)
                stats.count += 1

            last_item = item
            stats.add_tags(qs)

        stats.tags = [
            (name, count, count / stats.count * 100)
            for name, count in stats.tags.items()
        ]
        stats.tags.sort(key=lambda s: s[0])
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

    def get(self, request = None, **kwargs):
        if not request.user.is_active:
            return Http404()

        self.request = request
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)



