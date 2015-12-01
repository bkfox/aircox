from django.conf.urls import url, include

from website.models import *
from website.views import *

from aircox.cms.models import Article
from aircox.cms.views import Menu, Section, Sections
from aircox.cms.routes import *
from aircox.cms.website import Website


website = Website(
    name = 'RadioCampus',
    styles = 'website/styles.css',

    menus = [
        Menu(
            position = 'header',
            sections = [
                Sections.Image(url = 'website/logo.png'),
                Sections.Image(url = 'website/colony.png', attrs = { 'id': 'colony' }),
            ]
        ),

        Menu(
            position = 'top',
            sections = [
                Section(content = "Radio Campus le SITE"),
            ]
        ),

        Menu(
            position = 'left',
            sections = [
                Section(content = 'loool<br>blob'),
                PreviousDiffusions(),
            ],
        ),
    ],
)

base_sections = [
    Sections.PostContent(),
    Sections.PostImage(),
]

base_routes =  [
    AllRoute,
    ThreadRoute,
    SearchRoute,
    DateRoute,
]

website.register(
    'article',
    Article,
    sections = base_sections,
    routes = base_routes
)

website.register(
    'program',
    Program,
    sections = base_sections + [
        ScheduleSection(),
        EpisodesSection(),
    ],
    routes = base_routes,
)

website.register (
    'episode',
    Episode,
    sections = base_sections,
    routes = base_routes,
)

urlpatterns = website.urls

