from django.contrib import admin
from django.utils.translation import ugettext_lazy as _

from . import viewsets
from aircox.viewsets import SoundViewSet
from .views import StreamerAdminMixin


admin.site.route_view('tools/streamer', StreamerAdminMixin.as_view(),
                      'tools-streamer', label=_('Streamer Monitor'))

streamer_prefix = 'streamer/(?P<station_pk>[0-9]+)/'


router = admin.site.router
router.register(streamer_prefix + 'playlist', viewsets.PlaylistSourceViewSet,
    basename='streamer-playlist')
router.register(streamer_prefix + 'queue', viewsets.QueueSourceViewSet,
    basename='streamer-queue')
router.register('streamer', viewsets.StreamerViewSet, basename='streamer')
router.register('sound', SoundViewSet, basename='sound')

urls = []

