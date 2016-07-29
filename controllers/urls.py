
from django.conf.urls import include, url
import aircox.controllers.views as views

urls = [
    url(r'^monitor', views.Monitor.as_view(), name='controllers.monitor'),
    url(r'^on_air', views.on_air, name='controllers.on_air'),
]

