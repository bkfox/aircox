import re

from django.views.generic.base import View, TemplateResponseMixin
from django.template.loader import render_to_string
from django.shortcuts import render
from django.http import HttpResponse

import aircox_liquidsoap.settings as settings
import aircox_liquidsoap.utils as utils
import aircox_programs.models as models

class LiquidControl (View):
    template_name = 'aircox_liquidsoap/controller.html'

    def get_context_data (self, **kwargs):
        stations = models.Station.objects.all()
        controller = utils.Controller()

        for station in stations:
            name = station.get_slug_name()
            streams = models.Stream.objects.filter(
                program__active = True,
                program__station = station
            )

            # list sources
            sources = [ 'dealer' ] + \
                      [ stream.program.get_slug_name() for stream in streams]

            # sources status
            station.sources = { name: controller.get(station) }
            station.sources.update({
                source: controller.get(station, source)
                for source in sources
            })

        return {
            'request': self.request,
            'stations': stations,
        }

    def get (self, request = None, **kwargs):
        self.request = request
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)


