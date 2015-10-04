from django.conf.urls import url, include

from website.models import *
from website.views import *

from aircox_cms.models import Article
from aircox_cms.views import Menu, Section, Sections, ViewSet
from aircox_cms.routes import *
from aircox_cms.website import Website

class ProgramSet (ViewSet):
    model = Program
    list_routes = [
        AllRoute,
        ThreadRoute,
        SearchRoute,
        DateRoute,
    ]

    detail_sections = ViewSet.detail_sections + [
        ScheduleSection,
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
    styles = 'website/styles.css',

    menus = [
        Menu(
            position = 'header',
            sections = [
                Sections.Image(url = 'website/logo.png'),
                Sections.Image(url = 'website/colony.png', classes='colony'),
            ]
        ),

        Menu(
            position = 'top',
            sections = [
                Section(content = "Radio Campus le SITE")
            ]
        ),

        Menu(
            position = 'left',
            sections = [
                Section(content = 'loool<br>blob')
            ],
        ),
    ],
)

website.register_set(ProgramSet)
website.register_set(EpisodeSet)
website.register_set(ArticleSet)
urlpatterns = website.urls

