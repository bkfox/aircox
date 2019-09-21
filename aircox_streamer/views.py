from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from aircox.views.admin import BaseAdminView


class StreamerAdminView(BaseAdminView, TemplateView):
    template_name = 'aircox_streamer/streamer.html'
    title = _('Streamer Monitor')


