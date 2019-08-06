import pytz
from django.db.models import Q
from django.utils import timezone as tz

from .models import Station
from .utils import Redirect


__all__ = ['AircoxMiddleware']


class AircoxMiddleware(object):
    """
    Middleware used to get default info for the given website. Theses
    This middleware must be set after the middleware
        'django.contrib.auth.middleware.AuthenticationMiddleware',
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def get_station(self, request):
        """ Return station for the provided request """
        expr = Q(default=True) | Q(hosts__contains=request.get_host())
        # case = Case(When(hosts__contains=request.get_host(), then=Value(0)),
        #            When(default=True, then=Value(32)))
        return Station.objects.filter(expr).order_by('default').first()
        #              .annotate(resolve_priority=case) \
        # .order_by('resolve_priority').first()

    def init_timezone(self, request):
        # note: later we can use http://freegeoip.net/ on user side if
        # required
        timezone = None
        try:
            timezone = request.session.get('aircox.timezone')
            if timezone:
                timezone = pytz.timezone(timezone)
        except:
            pass

        if not timezone:
            timezone = tz.get_current_timezone()
            tz.activate(timezone)

    def __call__(self, request):
        self.init_timezone(request)
        request.station = self.get_station(request)
        try:
            return self.get_response(request)
        except Redirect:
            return
