from django.conf.urls import url
from django.urls import path, register_converter

from . import views, models
from .converters import PagePathConverter, DateConverter, WeekConverter

register_converter(PagePathConverter, 'page_path')
register_converter(DateConverter, 'date')
register_converter(WeekConverter, 'week')

urlpatterns = [
    path('programs/<slug:slug>/',
        views.ProgramPageView.as_view(), name='program-page'),
    path('programs/<slug:program_slug>/diffusions/',
         views.DiffusionsView.as_view(), name='diffusion-list'),

    path('diffusion/<slug:slug>/',
        views.ProgramPageView.as_view(), name='diffusion-page'),

    path('diffusions/',
         views.TimetableView.as_view(), name='timetable'),
    path('diffusions/<week:date>/',
         views.TimetableView.as_view(), name='timetable'),
    path('diffusions/all',
         views.DiffusionsView.as_view(), name='diffusion-list'),
    path('logs/', views.LogsView.as_view(), name='logs'),
    path('logs/<date:date>/', views.LogsView.as_view(), name='logs'),
    path('<page_path:path>', views.route_page, name='page'),
]

