from django.conf.urls import url
from django.urls import path, register_converter

from . import views, models
from .converters import PagePathConverter, DateConverter

register_converter(PagePathConverter, 'page_path')
register_converter(DateConverter, 'date')

urlpatterns = [
    path('diffusions/',
         views.TimetableView.as_view(), name='timetable'),
    path('diffusions/<date:date>',
         views.TimetableView.as_view(), name='timetable'),
    path('diffusions/all',
         views.DiffusionsView.as_view(), name='diffusion-list'),
    path('diffusions/<slug:program>',
         views.DiffusionsView.as_view(), name='diffusion-list'),
    path('logs/', views.LogsView.as_view(), name='logs'),
    path('logs/<date:date>', views.LogsView.as_view(), name='logs'),
    path('<page_path:path>', views.route_page, name='page'),
]

