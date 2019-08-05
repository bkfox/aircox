from django.urls import path, register_converter
from django.utils.translation import ugettext_lazy as _

from . import views
from .converters import PagePathConverter, DateConverter, WeekConverter


register_converter(PagePathConverter, 'page_path')
register_converter(DateConverter, 'date')
register_converter(WeekConverter, 'week')


#urls = [
#    path('on_air', views.on_air, name='aircox.on_air'),
#    path('monitor', views.Monitor.as_view(), name='aircox.monitor'),
#    path('stats', views.StatisticsView.as_view(), name='aircox.stats'),
#]


urls = [
    path(_('programs/<slug:slug>/'),
         views.ProgramDetailView.as_view(), name='program-detail'),
    path(_('programs/<slug:program_slug>/episodes/'),
         views.DiffusionListView.as_view(), name='diffusion-list'),

    path(_('episodes/'),
         views.DiffusionListView.as_view(), name='diffusion-list'),
    path(_('episodes/week/'),
         views.TimetableView.as_view(), name='timetable'),
    path(_('episodes/week/<week:date>/'),
         views.TimetableView.as_view(), name='timetable'),
    path(_('episodes/<slug:slug>/'),
         views.EpisodeDetailView.as_view(), name='episode-detail'),

    path(_('logs/'), views.LogListView.as_view(), name='logs'),
    path(_('logs/<date:date>/'), views.LogListView.as_view(), name='logs'),
    # path('<page_path:path>', views.route_page, name='page'),
]


