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
        tags = None
        """
        Total of played track's tags: [(tag_name, tag_count, tag_average), ...]
        on the station for the given date. Note: tag_average is in %
        """
        tracks_count = 0

        def __init__(self, **kwargs):
            self.items = []
            self.tags = []
            self.__dict__.update(kwargs)

    def get_stats(self, station, date):
        """
        Return statistics for the given station and date.
        """
        items = station.on_air(date)
        stats = self.Stats(station = station, items = items, date = date)

        sums = {}
        total = 0

        for item in items:
            qs = models.Track.objects.get_for(item)
            item.tracks = qs
            item.tracks_count = qs.count()

            qs = qs.values('tags__name').annotate(count = Count('tags__name')) \
                    .order_by('tags__name')
            item.tags = [
                (q['tags__name'], q['count'])
                for q in qs if q['tags__name']
            ]
            for name, count in item.tags:
                sums[name] = (sums.get(name) or 0) + count

            total += item.tracks_count

        stats.tracks_count = total
        stats.tags = [
            (name, count, count / total * 100)
            for name, count in sums.items()
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



