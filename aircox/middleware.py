import pytz
import django.utils.timezone as tz

import aircox.models as models


class AircoxInfo:
    """
    Used to store informations about Aircox on a request. Some of theses
    information are None when user is anonymous.
    """
    station = None
    """
    Current station
    """
    default_station = False
    """
    Default station is used as the current station
    """

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class AircoxMiddleware(object):
    """
    Middleware used to get default info for the given website. Theses
    This middleware must be set after the middleware
        'django.contrib.auth.middleware.AuthenticationMiddleware',
    """
    default_qs = models.Station.objects.filter(default = True)

    def __init__(self, get_response):
        self.get_response = get_response

    def init_station(self, request, aircox):
        # update current station
        station = request.GET.get('aircox.station')
        pk = None
        try:
            if station:
                pk = request.GET['aircox.station']
                if station:
                    pk = int(pk)
                    if models.Station.objects.filter(pk = station).exists():
                        request.session['aircox.station'] = pk
        except:
            pass

        # select current station
        station = None
        pk = None
        try:
            pk = request.session.get('aircox.station')
            if pk:
                pk = int(pk)
                station = models.Station.objects.filter(pk = pk).first()
        except:
            pass

        if not station:
            pk = None
            station = self.default_qs.first() or \
                        models.Station.objects.first()

        aircox.station = station
        aircox.default_station = (pk is None)

    def init_timezone(self, request, aircox):
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
        tz.activate(pytz.timezone('Europe/Brussels'))
        aircox = AircoxInfo()

        if request.user.is_authenticated():
            self.init_station(request, aircox)
        self.init_timezone(request, aircox)

        request.aircox = aircox
        return self.get_response(request)


