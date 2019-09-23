from django.urls import include, path, register_converter
from django.utils.translation import ugettext_lazy as _

from rest_framework.routers import DefaultRouter

from . import models, views, viewsets
from .converters import PagePathConverter, DateConverter, WeekConverter


__all__ = ['api', 'urls']


register_converter(PagePathConverter, 'page_path')
register_converter(DateConverter, 'date')
register_converter(WeekConverter, 'week')


# urls = [
#    path('on_air', views.on_air, name='aircox.on_air'),
#    path('monitor', views.Monitor.as_view(), name='aircox.monitor'),
#    path('stats', views.StatisticsView.as_view(), name='aircox.stats'),
# ]


router = DefaultRouter()
router.register('sound', viewsets.SoundViewSet, basename='sound')


api = [
    path('logs/', views.LogListAPIView.as_view(), name='live'),
] + router.urls


urls = [
    path('', views.HomeView.as_view(), name='home'),
    path('api/', include((api, 'aircox'), namespace='api')),

    # path('', views.PageDetailView.as_view(model=models.Article),
    #     name='home'),
    path(_('articles/'),
         views.ArticleListView.as_view(model=models.Article, is_static=False),
         name='article-list'),
    path(_('articles/<slug:slug>/'),
         views.ArticleDetailView.as_view(),
         name='article-detail'),

    path(_('episodes/'),
         views.EpisodeListView.as_view(), name='episode-list'),
    path(_('episodes/<slug:slug>/'),
         views.EpisodeDetailView.as_view(), name='episode-detail'),
    path(_('week/'),
         views.DiffusionListView.as_view(), name='diffusion-list'),
    path(_('week/<date:date>/'),
         views.DiffusionListView.as_view(), name='diffusion-list'),

    path(_('logs/'), views.LogListView.as_view(), name='log-list'),
    path(_('logs/<date:date>/'), views.LogListView.as_view(), name='log-list'),
    # path('<page_path:path>', views.route_page, name='page'),

    path(_('publications/'),
         views.PageListView.as_view(model=models.Page), name='page-list'),

    path(_('programs/'), views.ProgramListView.as_view(model=models.Program),
         name='program-list'),
    path(_('programs/<slug:slug>/'),
         views.ProgramDetailView.as_view(), name='program-detail'),
    path(_('programs/<slug:parent_slug>/episodes/'),
         views.EpisodeListView.as_view(), name='episode-list'),
    path(_('programs/<slug:parent_slug>/articles/'),
         views.ArticleListView.as_view(), name='article-list'),
    path(_('programs/<slug:parent_slug>/publications/'),
         views.ProgramPageListView.as_view(), name='program-page-list'),
]

