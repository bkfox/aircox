from django.conf.urls import url, include

from website.models import *
from website.views import *
from website.routes import *


routes = Routes()

routes.register( SearchRoute(Article, PostListView) )
#routes.register( SearchRoute(ProgramPost, PostListView, base_name = 'programs') )
#routes.register( SearchRoute(EpisodePost, PostListView, base_name = 'episodes') )

routes.register( ThreadRoute(Article, PostListView) )
#routes.register( ThreadRoute(ProgramPost, PostListView, base_name = 'programs') )
#routes.register( ThreadRoute(EpisodePost, PostListView, base_name = 'episodes') )

routes.register( DateRoute(Article, PostListView) )
#routes.register( DateRoute(ProgramPost, PostListView, base_name = 'programs') )
#routes.register( DateRoute(EpisodePost, PostListView, base_name = 'episodes') )

urlpatterns = routes.get_urlpatterns()


