from django.conf.urls import url

from . import views

urlpatterns = [
    url(r"^(?P<path>[-\w/]+)/$", views.page_detail, name="page"),
    url(r"^$", views.page_detail, name="root"),
]

