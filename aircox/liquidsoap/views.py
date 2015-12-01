import re

from django.views.generic.base import View, TemplateResponseMixin
from django.template.loader import render_to_string
from django.shortcuts import render
from django.http import HttpResponse

import aircox.liquidsoap.settings as settings
import aircox.liquidsoap.utils as utils
import aircox.programs.models as models


view_monitor = utils.Monitor(
    utils.Connector(address = settings.AIRCOX_LIQUIDSOAP_SOCKET)
)

class Actions:
    @classmethod
    def exec (cl, monitor, controller, source, action):
        controller = monitor.controllers.get(controller)
        source = controller and controller.get(source)

        if not controller or not source or \
                action.startswith('__') or \
                action not in cl.__dict__:
            return -1

        action = getattr(Actions, action)
        return action(monitor, controller, source)

    @classmethod
    def skip (cl, monitor, controller, source):
        source.skip()


class LiquidControl (View):
    template_name = 'aircox_liquidsoap/controller.html'

    def get_context_data (self, **kwargs):
        view_monitor.update()
        return {
            'request': self.request,
            'monitor': view_monitor,
            'embed': 'embed' in self.request.GET,
        }

    def post (self, request = None, **kwargs):
        if 'action' in request.POST:
            POST = request.POST
            controller = POST.get('controller')
            source = POST.get('source')
            action = POST.get('action')
            Actions.exec(view_monitor, controller, source, action)
        return HttpResponse('')

    def get (self, request = None, **kwargs):
        self.request = request
        context = self.get_context_data(**kwargs)
        return render(request, self.template_name, context)


