from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^(?P<path>[-\w/]+)/$", views.route_page, name="page"),
    url(r"^$", views.route_page, name="root"),
]

