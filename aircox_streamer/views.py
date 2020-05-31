from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView

from aircox.views.admin import AdminMixin


class StreamerAdminMixin(AdminMixin, TemplateView):
    template_name = 'aircox_streamer/streamer.html'
    title = _('Streamer Monitor')


