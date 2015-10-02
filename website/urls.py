from django.conf.urls import url, include

from website.models import *
from website.views import *

from cms.models import Article
from cms.views import ViewSet, Menu
from cms.routes import *

class ProgramSet (ViewSet):
    model = Program
    list_routes = [
        AllRoute,
        ThreadRoute,
        SearchRoute,
        DateRoute,
    ]

    detail_sections = [
        ScheduleSection
    ]

class EpisodeSet (ViewSet):
    model = Episode
    list_routes = [
        AllRoute,
        ThreadRoute,
        SearchRoute,
        DateRoute,
    ]

class ArticleSet (ViewSet):
    model = Article
    list_routes = [
        AllRoute,
        ThreadRoute,
        SearchRoute,
        DateRoute,
    ]


website = Website(
    name = 'RadioCampus',
    menus = [
        Menu(
            position = 'top',
            sections = []
        )
    ],
})


website.register_set(ProgramSet)
website.register_set(EpisodeSet)
website.register_set(ArticleSet)
urlpatterns = website.urls

