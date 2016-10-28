from django.conf.urls import include, url
import aircox.views as views

urls = [
    url(r'^on_air', views.on_air, name='aircox.on_air'),
    url(r'^monitor', views.Monitor.as_view(), name='aircox.monitor'),
    url(r'^stats', views.StatisticsView.as_view(), name='aircox.stats'),
]

