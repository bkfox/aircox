from django.conf.urls import url, include

from website.models import *
from website.views import *
from website.routes import *


class ProgramSet (ViewSet):
    model = ProgramPost
    name = 'programs'

    list_routes = [
        ThreadRoute,
        SearchRoute,
        DateRoute,
    ]


class EpisodeSet (ViewSet):
    model = EpisodePost
    name = 'episodes'

    list_routes = [
        ThreadRoute,
        SearchRoute,
        DateRoute,
    ]


class ArticleSet (ViewSet):
    model = Article
    list_routes = [
        ThreadRoute,
        SearchRoute,
        DateRoute,
    ]


router = Router()
router.register_set(ProgramSet())
router.register_set(EpisodeSet())
router.register_set(ArticleSet())

urlpatterns = router.get_urlpatterns()


