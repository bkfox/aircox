import json

from django.views.generic.base import View, TemplateResponseMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils import timezone as tz

import aircox.controllers.models as models


class Stations:
    stations = models.Station.objects.all()
    update_timeout = None
    fetch_timeout = None

    def fetch(self):
        if self.fetch_timeout and self.fetch_timeout > tz.now():
            return

        self.fetch_timeout = tz.now() + tz.timedelta(seconds = 5)
        for station in self.stations:
            station.prepare(fetch = True)

stations = Stations()


def on_air(request):
    try:
        import aircox.cms.models as cms
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
            'title': publication.title if publication else last.program.name,
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

    def get (self, request = None, **kwargs):
        if not request.user.is_active:
            return Http404()

        self.request = request
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)

    def post (self, request = None, **kwargs):
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
            source = station.source_set.filter(name = POST['source']) \
                            .first()
            if not source and POST['source'] == station.dealer.name:
                source = station.dealer

            if source:
                source.prepare()

        if station and action == 'skip':
            if source:
                print('skip ', source)
                source.controller.skip()
            else:
                station.controller.skip()

        return HttpResponse('')



