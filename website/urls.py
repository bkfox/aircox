from django.conf.urls import url, include

from website.models import *
from website.views import *

from cms.models import Article
from cms.views import ViewSet
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

router = Router()
router.register_set(ProgramSet())
router.register_set(EpisodeSet())
router.register_set(ArticleSet())

urlpatterns = router.get_urlpatterns()


